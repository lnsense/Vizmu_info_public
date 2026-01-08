import streamlit as st
import os
import openai
from openai import OpenAI
from PyPDF2 import PdfReader
import json
import re
import time
import chromadb
import webbrowser
import openpyxl
import auth
from datetime import datetime
import numpy as np
import pandas as pd
from streamlit_gsheets import GSheetsConnection
#Úgy néz ki elég a page setupnál inicializálni a session state username-et és az a többi pagen is behívható, Remélhetőleg cookie-hoz rendelve marad... Ha nem próba cooki alapján tárolást megnézni ugyanígy?
##print(st.session_state['username'])

keresesek_szama = 100
##kerdes = "Mennyibe kerül a szakfelügyelet megrendelése?"

try:
    # client = chromadb.PersistentClient(path=r"KERESO_DATA")
    client = chromadb.CloudClient(
        api_key=st.secrets["ChromaDB_API_key"]["chroma-secret-key"],
        tenant="7f72c342-a9b5-4289-8e24-834b9d8ec6a1",
        database="Vizmuvek_Tudasbazis"
    )
    # collection = client.get_collection(name="TRV_szabalyzat")
    # print(client.heartbeat())
    # print(collection.count())
    # print(collection.peek())
    # print("------------------")

    # with open(r"C:\ins\Vector_DB\config.txt", mode="r") as json_file:
    #     config_data = json.load(json_file)
    # openai.api_key = config_data.get("openai-secret-key")


    openai.api_key = st.secrets["OpenAI_API_key"]["openai-secret-key"]



    AI_client = OpenAI(
        api_key=openai.api_key,
    )
except Exception as e:
    pass


#Ez még sajnos nem működik, át kell majd dolgozni a visszajelzések pontosítása érdekében!
# Check if the user is logged in
##username = auth.check_login()
##
##if 'username' not in st.session_state:
##    st.session_state['username'] = ""
##st.session_state['username'] = username


# Később felhaszánlói query elemzés, módosítás, kulcszavas, szinonímás kinyerés.
# Akár saját adatbázis kialakítása a gyakori témákról, ahhoz összevetni a kérdéseket.

@st.cache_data(ttl = None, max_entries = 15000, show_spinner = False)
def jsonify_user_question(kerdes):
    assistant = AI_client.chat.completions.create(            
                model="gpt-5-nano",
                # temperature= 0.1,
                response_format={ "type": "json_object" },
                messages=[
                {"role": "system", "content": """Kapni fogsz egy mondatot/kérdést. A Te feladatod, hogy a megadott adatokból kinyerd egy vektoros adatbázis embedding alapú kereséséhez szükséges kulcsszavakat.
                                                A válaszodat kizárólag JSON formátumban, az alábbi feltételekkel add meg:
                                                {
                                                    "kulcsszo": "*kinyert kulcsszó*", #törekedj rövid kulcsszóra, a fő szó, téma meghatározására, ami alapján keresni lehet. Ha egyszerre több témára kívánnak keresni, vesszővel elválasztva írd le a témákat. Kötelező megadni.
                                                    "kornyezet": "*kinyert kulcsszó környezete*" #opcionálisan megadható információ a keresés pontosítása érdekében. Olyan kulcsszavakat adj meg itt, ami alapján behatárolható, hogy a fő kulcsszó/téma milyen környezetben értelmezendő, mire irányul a kérdés. Adhatsz meg több értéket is, vesszővel elválasztva.
                                                }
                                                
                                                Például:
                                                Kérdés: "Mik az oltóvíz bekötéssel kapcsolatos előírások?"
                                                Válasz:
                                                {
                                                    "kulcsszo": "oltóvíz bekötés",
                                                    "kornyezet": "előírás"
                                                }
                                                
                                                Kérdés: "Mennyibe kerül a szakfelügyelet megrendelés?"
                                                Válasz:
                                                {
                                                    "kulcsszo": "szakfelügyelet",
                                                    "kornyezet": "ár, díj, költség"
                                                }
                                                """},
                {"role": "user", "content": f"felhasználó kérdése amiből embedding alapú keresésre alkalmas kulcsszót kell kinyerned: {kerdes}"},
              ]
            )
           
    # print(f"{kerdes}\n\n")

    response = assistant.choices[0].message.content
    response = response.lower()
    token_usage = assistant.usage
    # print(f"{token_usage}\n\n")
    print(f"kérdés átfogalmazva: \n{response}")
    return response


def refactor_question(kerdes):
    
        response = jsonify_user_question(kerdes)
        data = json.loads(response)
        kulcsszo = data.get("kulcsszo")
        kornyezet = data.get("kornyezet")
    
        kerdes = f"{kulcsszo}, {kornyezet}"
        return kerdes
        # print("kulcsszo:", kulcsszo)
        # print("kornyezet:", kornyezet) 
##kerdes = refactor_question(kerdes)
##print(kerdes)

def refactor_question_keyword_only(kerdes):
    
        response = jsonify_user_question(kerdes)
        data = json.loads(response)
        kulcsszo = data.get("kulcsszo")
    
        kerdes = f"{kulcsszo}"
        return kerdes



def find_all_relevant_documents(kerdes, doc, metadatas, meta_id):
    kerdes = kerdes.lower()
    
    all_relevant_documents = []
    valaszok = []
    eleresi_helyek = []
    oldalszamok = []
    nevek = []    
    ids = []

    for i in range(keresesek_szama):  # Adjust the range if the number of valaszok per doc varies
            if i < len(doc):  # Ensure the index exists in the doc
                valaszok.append(doc[i])  # Append each valasz
                eleresi_helyek.append(metadatas[i]['Elérési hely'])
                oldalszamok.append(metadatas[i]['Oldalszám'])
                nevek.append(metadatas[i]['Név'])                
                ids.append(meta_id[i])
                all_relevant_documents = [list(item) for item in zip(valaszok, eleresi_helyek, oldalszamok, nevek, ids)]

    return all_relevant_documents



#Ehhez majd implementálni kell fuzzy search-et is, typokhoz. 

def find_exact_matches(kerdes, doc, metadatas, meta_id, keresesek_szama):
    kerdes = kerdes.lower()
    
    exact_matches = []
    valaszok = []
    eleresi_helyek = []
    oldalszamok = []
    nevek = []
    ids = []
    
    # for i in range(keresesek_szama):  # Adjust the range if the number of valaszok per doc varies
    limit = min(keresesek_szama, len(doc), len(metadatas), len(meta_id))
    for i in range(limit):
        exact_match = re.search(kerdes, doc[i].lower()) #implement typos later
        if exact_match:
            valaszok.append(doc[i])  # Append each valasz
            eleresi_helyek.append(metadatas[i]['Elérési hely'])
            oldalszamok.append(metadatas[i]['Oldalszám'])
            nevek.append(metadatas[i]['Név'])
            ids.append(meta_id[i])
            exact_matches = [list(item) for item in zip(valaszok, eleresi_helyek, oldalszamok, nevek, ids)]

    # if exact_matches == []:
    #     exact_matches = None
    return exact_matches


#Ehhez majd implementálni kell fuzzy search-et is, typokhoz. 

def find_partial_matches(kerdes, doc, metadatas, meta_id, keresesek_szama):
    kerdes = kerdes.lower().lstrip()
    original_kerdes = kerdes
    filler_words = [
        "a",
        "az",
        "hogy",
        "lehet",
        "lehet, hogy",
        "lehet hogy",
        "és",
        "es",
        "is",
        "valahogy",
        "kell",
        "mi",
        "milyen",
        "miért",
        "hogyan",
        "ki",
        "hány",
        "mennyi",
        "hol",
        "hova",
        "hová",
        "meddig",
        "hát",
        "szóval",
        "ugye",
        "amúgy",
        "na",
        "nos",
        "akkor",
        "azért",
        "úgy",
        "így",
        "ilyen",
        "olyan",
        "egyébként",
        "nagyon",
        "kicsit",
        "viszont",
        "de",
        "ja",
        "ok",
        "oksa",
        "oké",
        "?",
        ":",
        ",",
        ".",
        "-"        
    ]
    sanitized_kerdes = kerdes
    filler_words_sorted = sorted(filler_words, key=len, reverse=True)
    while sanitized_kerdes:
        removed = False
        for filler in filler_words_sorted:
            pattern = rf"^{re.escape(filler)}(?:[\s.,?!]+|$)"
            match = re.match(pattern, sanitized_kerdes, flags=re.IGNORECASE)
            if match:
                sanitized_kerdes = sanitized_kerdes[match.end():].lstrip()
                removed = True
                break
        if not removed:
            break
    kerdes = sanitized_kerdes if sanitized_kerdes else original_kerdes
    
    partial_matches = []
    valaszok = []
    eleresi_helyek = []
    oldalszamok = []
    nevek = []    
    ids = []
        
    # for i in range(keresesek_szama):
    limit = min(keresesek_szama, len(doc), len(metadatas), len(meta_id))
    for i in range(limit):
        for j in reversed(range(len(kerdes))):
            partial_match = re.search(kerdes[:j], doc[i].lower())
            if partial_match:
                valaszok.append(doc[i])
                eleresi_helyek.append(metadatas[i]['Elérési hely'])
                oldalszamok.append(metadatas[i]['Oldalszám'])
                nevek.append(metadatas[i]['Név'])                
                ids.append(meta_id[i])
                partial_matches = [list(item) for item in zip(valaszok, eleresi_helyek, oldalszamok, nevek, ids)]
                break
            if j == 5:
                break
    return partial_matches

# partial_matches = find_partial_matches(kerdes= "tüzivíz célú bekötőve",
#                                        doc = ["asdfasdf", "tüzivdasfégknafdsélgn", "dkfnmasdklégn"],
#                                        metadatas = ["url1", "url2", "url3"],
#                                        meta_id = ["id1", "id2", "id3"])
# print(partial_matches)


def rearrange_matches(all_relevant_documents, exact_matches, partial_matches):
    
    valaszok = []
    if len(exact_matches) >=1:
        valaszok = exact_matches

    if len(partial_matches) >=1:
        for valasz in all_relevant_documents[:15]:
            if valasz in partial_matches:
                valaszok.append(valasz)
        for valasz in all_relevant_documents[:10]:
            valaszok.append(valasz)
    if len(valaszok) <= 30:
        for valasz in all_relevant_documents[:30]:
            valaszok.append(valasz)
    return valaszok


def remove_duplicates(lst):
    # Set to keep track of seen sublists (as tuples)
    seen = set()
    # List to store unique sublists
    result = []
    
    # Iterate through the original list
    for sublist in lst:
        # Convert the sublist to a tuple to make it hashable
        tuple_sublist = tuple(sublist)
        # If the tuple is not in seen, add to seen and result list
        if tuple_sublist not in seen:
            seen.add(tuple_sublist)
            result.append(sublist)
    
    # Return the result list without duplicates
    return result

# # Example usage
# my_list = [['a', '1', 'id1'], ['b', '2', 'id2'], ['c', '3', 'id3'], ['a', '1', 'id1'], ['d', '4', 'id4'], ['b', '2', 'id2'], ['e', '5', 'id5']]
# unique_list = remove_duplicates(my_list)
# print(unique_list)  # Output: [['a', '1', 'id1'], ['b', '2', 'id2'], ['c', '3', 'id3'], ['d', '4', 'id4'], ['e', '5', 'id5']]




        
@st.cache_data(ttl = "7d", max_entries = None, show_spinner = "Keresés...")
def find_matches(kerdes, keresesek_szama, collection_name):
    """
    Megkeresi a dokumentum, metaadat és id találatokat a kérdés alapján. 100 találat. Tartalomjegyzéknél duplán dolgozik... 
    Rerankolja a manuálisan felépített függvényekkel.
    
    """
    
    if len(kerdes) >= 20:
        kerdes = refactor_question(kerdes)
        
    kerdes = kerdes.lower()
    escaped_kerdes = re.escape(kerdes)
    
    kerdes_embed = AI_client.embeddings.create(
        input=kerdes,
        model="text-embedding-3-large"
    )
    # print(kerdes_embed)
    # print(len(kerdes_embed.data[0].embedding))
    if collection_name == "DRV_tajekoztato": # ezt majd törölni kell ha lesz több doksi a tájékoztatós adatbázisban
        keresesek_szama = 25

    collection = client.get_collection(name=collection_name)
    
    find_document = collection.query(
        query_embeddings=[kerdes_embed.data[0].embedding],
        n_results=keresesek_szama,
        include=["documents", "distances", "metadatas"]
    )
    # print(f"Találatok: {find_document}")


    for doc, metadatas, meta_id in zip(find_document["documents"], find_document["metadatas"], find_document["ids"]): # Nincs ennél gyorsabb megoldás? Összes metadata helyett csak az elérési helyeket loopolni?
        all_relevant_documents = find_all_relevant_documents(kerdes, doc, metadatas, meta_id)
        # for valasz in all_relevant_documents:
        #     print("\n\n\n\n ------------------------ RELEVANT DOCUMENT --------------------------- \n\n\n\n")
        #     print(valasz)
        
        exact_matches = find_exact_matches(kerdes, doc, metadatas, meta_id, keresesek_szama)
        # print(exact_matches)
        # print(len(exact_matches))
        # if len(exact_matches) >= 1:
            # for valasz in exact_matches: 
            #     print("\n\n\n\n ------------------------ EXACT MATCH --------------------------- \n\n\n\n")
            #     print(valasz)              
        if len(exact_matches) <= 5:
            partial_matches = find_partial_matches(kerdes, doc, metadatas, meta_id, keresesek_szama)
            # print(partial_matches)
        else:
            partial_matches = []
            # print(partial_matches)
            
        # for valasz in partial_matches: 
        #     print("\n\n\n\n ------------------------ PARTIAL MATCH -------------------------- \n\n\n\n")
        #     print(valasz)
            

    rearranged_matches = rearrange_matches(all_relevant_documents, exact_matches, partial_matches)
    # for valasz in rearranged_matches:
    #     print("\n\n\n\n --------------------------------------------------- \n\n\n\n")
    #     print(valasz)
##    print(len(rearranged_matches))
    organized_matches = remove_duplicates(rearranged_matches)
    valaszok = [sublist[0] for sublist in organized_matches]
    eleresi_helyek = [sublist[1] for sublist in organized_matches]
    oldalszamok = [sublist[2] for sublist in organized_matches]
    nevek = [sublist[3] for sublist in organized_matches]   
    ids = [sublist[4] for sublist in organized_matches]
##    print(len(organized_matches))
    # for valasz in organized_matches[:5]:
    #     print("\n\n\n\n --------------------------------------------------- \n\n\n\n")
    #     print(valasz[0])


##
##    if collection_name == "DRV_tartalomjegyzek_szabalyzat":        
##        for idx, (valasz, eleresi_hely, id_) in enumerate(zip(valaszok[:5], eleresi_helyek[:5], ids[:5]), start=1):                
##                id_number = int(id_[2:]) 
##                tartalomjegyzek_db = collection.get(
##                    ids = [f"id{id_number}"],
##                    include=["documents", "metadatas"],
##                    )
##                oldalszam = tartalomjegyzek_db["metadatas"][0]["Oldalszám"]
##                oldalszamok.append(oldalszam)
##                nev = tartalomjegyzek_db["metadatas"][0]["Név"]
##                nevek.append(nev)
##    elif collection_name == "Jogszabaly_tartalomjegyzek":        
##        for idx, (valasz, eleresi_hely, id_) in enumerate(zip(valaszok[:5], eleresi_helyek[:5], ids[:5]), start=1):                
##                id_number = int(id_[2:]) 
##                tartalomjegyzek_db = collection.get(
##                    ids = [f"id{id_number}"],
##                    include=["documents", "metadatas"],
##                    )
##                oldalszam = tartalomjegyzek_db["metadatas"][0]["Oldalszám"]
##                oldalszamok.append(oldalszam)
##                nev = tartalomjegyzek_db["metadatas"][0]["Név"]
##                nevek.append(nev)


    return organized_matches, valaszok, eleresi_helyek, ids, oldalszamok, nevek


##organized_matches, valaszok, eleresi_helyek, ids = find_matches(kerdes, keresesek_szama)

# print(valaszok)


#EZT ÁT KELL DOLGOZNI AZ ÚJ KERESÉSI TALÁLATOKHOZ IGAZODJON!!! chunkolás átdolgozását követően (ne legyen 1 oldalon több "Oldalszám:")
def find_last_page_number_tajekoztato(id_number):
    
    collection = client.get_collection(name="DRV_tajekoztato")
    find_page_number_tajekoztato = collection.get(
        ids = [f"id{id_number}"],
        include=["documents"]
    )
    

    valaszok = []

    for doc  in zip(find_page_number_tajekoztato["documents"]):
        valaszok.append(doc)  # Append each valasz
    return valaszok



##@st.cache_data(ttl = "14d", max_entries = None, show_spinner = "Megválaszolás folyamatban...")
@st.cache_data(show_spinner = "Megválaszolás folyamatban...")
def ask_question_with_rag(kerdes, valaszok, ids, nev, oldalszam):
    model = "gpt-5-nano"
    # if selected_tab == "Szabályzat":
    #     id_data = "id 1-394: Üzletszabályzat, id 395-418: Árnyilvántartás"
    # if selected_tab == "Jogszabály":
    #     id_data = "id 1-187: Vksztv., id 188-373: Vksztv. végrehajtása. Idézésnél próbáld megadni a jogszabály paragrafusát is."
##        print(id_data)
##    if selected_tab == "Tájékoztató":
##        id_data = "id1 - id394: Üzletszabályzat, id395 - id418: Árnyilvántartás"    

    merged_data = list(zip(valaszok, nev, oldalszam))
    merged_data = json.dumps(
        [
            {"válasz": valasz, "forrás": dokumentum, "oldalszám": oldal}
            for valasz, dokumentum, oldal in zip(valaszok, nev, oldalszam)
        ],
        ensure_ascii=False
    )
    # print(merged_data)
    
    try:
        assistant = AI_client.chat.completions.create(            
            model=model,
            # temperature= 0.1,
            # reasoning_effort="minimal",
            messages=[
            {"role": "system", "content": """A DRV Zrt. víziközmű szolgáltató cég virtuális asszisztense vagy.
                                            Feladatod megválaszolni a cég belsős dolgozóinak kérdéseit a rendelkezésedre bocsátott adatok alapján.
                                            Egyszerre több forrásból is fogsz adatokat kapni, melyekből neked kell kinyerni a használható információt.
                                            A rendelkezésre álló adatok a kérdésre vonatkozó legközelebbi valószínűsíthető találatait adja meg, de nem biztos, hogy
                                            az első találatokban lesz a válasz.
                                            A találatok mellé megkapod a dokumentumok nevét és, hogy az adott információ hanyadik oldalon található meg az alábbi formátumban: [{"válasz": 'válasz1', "forrás": 'forrás1', "oldalszám": 'oldalszám1'}, {"válasz": 'válasz2', "forrás": 'forrás2', "oldalszám": 'oldalszám2'}, {"válasz": 'válasz3', "forrás": 'forrás3', "oldalszám": 'oldalszám3'}, ...]
                                            A kérdés megválaszolása után add meg, hogy a válaszod melyik dokumentumban és hanyadik oldalon található. Példa közvetlenül a válaszod után: "Forrás: Üzletszabályzat, 125. oldal". Ezt külön nem kell összefoglalnod, csak írd az adott talált információ után. Egynél többször ne írd le forrásokat.
                                            Ha több dokumentumban is található releváns információ, külön-külön add meg, hogy a válaszoknál melyik rész melyik dokumentumból származik.
                                            Próbálj minél pontosabban idézni. Nem kell yapping, tárgyra törő legyél, tényeket közölj. Fontos, hogy minél pontosabban idézd az eredeti szöveget. Fókuszálj a feltétett kérdés megválaszolására, valamint a keresett
                                            információ pontos megadására. Felesleges, nem a keresett témáról szóló információt ne adj meg. A felhasználónak ne magyarázkodj, hogy mit csinálsz, csak végezd el a feladatod. A véleményedet, megjegyzéseid tartsd magadban. A válaszod végén ne foglald össze a találatokat.
                                            """},
            {"role": "user", "content": f"A DRV Zrt. dolgozójának kérdése: {kerdes} \nRendelkezésre álló adatok: {merged_data}"},
          ]
        )

##        print(assistant)
##        print(f"Kérdés:\n{kerdes}\n\n")

        response = assistant.choices[0].message.content
        token_usage = assistant.usage
        # print(f"{token_usage}\n\n")
        return response, token_usage, model

    except Exception as e:
        return str(e), None, model

def costs(token_usage, model):

    if token_usage is None:
        return 0

    if model == "gpt-4o":
        cost_input = token_usage.prompt_tokens * 2.5 / 1000000
        cost_output = token_usage.completion_tokens * 10 / 1000000
        all_cost = cost_input + cost_output

        cost_input_HUF = cost_input*331
        cost_output_HUF = cost_output*331
        all_cost_HUF = all_cost*331
        
        # print(token_usage)
        # print(f"Input token: {token_usage.prompt_tokens}, Input cost: {cost_input} $, {cost_input * 376} Ft")
        # print(f"Output token: {token_usage.completion_tokens}, Output cost: {cost_output}$, {cost_output * 376} Ft")
        
        # print(f"All cost: {all_cost}$, {all_cost * 376} Ft")
        return all_cost_HUF

    if model == "gpt-4o-mini":
        cost_input = token_usage.prompt_tokens * 0.150 / 1000000
        cost_output = token_usage.completion_tokens * 0.600 / 1000000
        all_cost = cost_input + cost_output

        cost_input_HUF = cost_input*331
        cost_output_HUF = cost_output*331
        all_cost_HUF = all_cost*331
        
        # print(token_usage)
        # print(f"Input token: {token_usage.prompt_tokens}, Input cost: {cost_input} $, {cost_input * 376} Ft")
        # print(f"Output token: {token_usage.completion_tokens}, Output cost: {cost_output}$, {cost_output * 376} Ft")
        
        # print(f"All cost: {all_cost}$, {all_cost * 376} Ft")
        return all_cost_HUF

    if model == "gpt-5-nano":
        cost_input = token_usage.prompt_tokens * 0.05 / 1000000
        cost_output = token_usage.completion_tokens * 0.400 / 1000000
        all_cost = cost_input + cost_output

        cost_input_HUF = cost_input*331
        cost_output_HUF = cost_output*331
        all_cost_HUF = all_cost*331
        
        # print(token_usage)
        # print(f"Input token: {token_usage.prompt_tokens}, Input cost: {cost_input} $, {cost_input * 376} Ft")
        # print(f"Output token: {token_usage.completion_tokens}, Output cost: {cost_output}$, {cost_output * 376} Ft")
        
        # print(f"All cost: {all_cost}$, {all_cost * 376} Ft")
        return all_cost_HUF

#Ezt átdolgozni úgy, hogy ne szedje 3 típusra, csak a worksheetet változtassa valamelyik megadott paraméter alapján)
@st.cache_data(show_spinner = False)
def store_data_in_excel_szabalyzat(kerdes_szabalyzat, valasz_rag1_szabalyzat, valasz_rag2_szabalyzat, koltseg_rag1_szabalyzat, koltseg_rag2_szabalyzat, model, username):
    # Save data to Google Sheets (worksheet: "DRV_Szabályzat") via streamlit_gsheets
    try:
        conn = st.connection("gsheets_kereso", type=GSheetsConnection)
        df = conn.read(worksheet="DRV_Szabályzat", ttl=0)
    except Exception as e:
        st.error(f"Nem sikerült olvasni a Google Sheet-et: {e}")
        return

    current_datetime = datetime.now()

    # Build a new row aligned to existing headers
    cols = list(df.columns) if isinstance(df, pd.DataFrame) else []
    new_row = {c: "" for c in cols}

    def set_by_index(idx, value):
        if idx < len(cols):
            new_row[cols[idx]] = value

    # Map values by column positions to avoid header coupling
    set_by_index(0, kerdes_szabalyzat)
    set_by_index(1, valasz_rag1_szabalyzat)
    set_by_index(2, valasz_rag2_szabalyzat)
    set_by_index(3, koltseg_rag1_szabalyzat)
    set_by_index(4, koltseg_rag2_szabalyzat)
    set_by_index(5, model)
    set_by_index(10, current_datetime.strftime("%Y-%m-%d %H:%M:%S"))
    set_by_index(11, username)

    try:
        updated = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        conn.update(worksheet="DRV_Szabályzat", data=updated)
        print("Adatok lementve Google Sheet-be.")
    except Exception as e:
        st.error(f"Nem sikerült írni a Google Sheet-be: {e}")


@st.cache_data(show_spinner = False)
def store_data_in_excel_jogszabaly(kerdes_jogszabaly, valasz_rag1_jogszabaly, valasz_rag2_jogszabaly, koltseg_rag1_jogszabaly, koltseg_rag2_jogszabaly, model, username):
    # Save data to Google Sheets (worksheet: "DRV_Jogszabály") via streamlit_gsheets
    try:
        conn = st.connection("gsheets_kereso", type=GSheetsConnection)
        df = conn.read(worksheet="DRV_Jogszabály", ttl=0)
    except Exception as e:
        st.error(f"Nem sikerült olvasni a Google Sheet-et: {e}")
        return

    current_datetime = datetime.now()

    cols = list(df.columns) if isinstance(df, pd.DataFrame) else []
    new_row = {c: "" for c in cols}

    def set_by_index(idx, value):
        if idx < len(cols):
            new_row[cols[idx]] = value

    set_by_index(0, kerdes_jogszabaly)
    set_by_index(1, valasz_rag1_jogszabaly)
    set_by_index(2, valasz_rag2_jogszabaly)
    set_by_index(3, koltseg_rag1_jogszabaly)
    set_by_index(4, koltseg_rag2_jogszabaly)
    set_by_index(5, model)
    set_by_index(10, current_datetime.strftime("%Y-%m-%d %H:%M:%S"))
    set_by_index(11, username)

    try:
        updated = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        conn.update(worksheet="DRV_Jogszabály", data=updated)
        print("Adatok lementve Google Sheet-be.")
    except Exception as e:
        st.error(f"Nem sikerült írni a Google Sheet-be: {e}")

        
@st.cache_data(show_spinner = False)
def store_data_in_excel_tajekoztato(kerdes_tajekoztato, valasz_rag1_tajekoztato, valasz_rag2_tajekoztato, koltseg_rag1_tajekoztato, koltseg_rag2_tajekoztato, model, username):
    # Save data to Google Sheets (worksheet: "DRV_Tájékoztató") via streamlit_gsheets
    try:
        conn = st.connection("gsheets_kereso", type=GSheetsConnection)
        df = conn.read(worksheet="DRV_Tájékoztató", ttl=0)
    except Exception as e:
        st.error(f"Nem sikerült olvasni a Google Sheet-et: {e}")
        return

    current_datetime = datetime.now()

    cols = list(df.columns) if isinstance(df, pd.DataFrame) else []
    new_row = {c: "" for c in cols}

    def set_by_index(idx, value):
        if idx < len(cols):
            new_row[cols[idx]] = value

    set_by_index(0, kerdes_tajekoztato)
    set_by_index(1, valasz_rag1_tajekoztato)
    set_by_index(2, valasz_rag2_tajekoztato)
    set_by_index(3, koltseg_rag1_tajekoztato)
    set_by_index(4, koltseg_rag2_tajekoztato)
    set_by_index(5, model)
    set_by_index(10, current_datetime.strftime("%Y-%m-%d %H:%M:%S"))
    set_by_index(11, username)

    try:
        updated = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        conn.update(worksheet="DRV_Tájékoztató", data=updated)
        print("Adatok lementve Google Sheet-be.")
    except Exception as e:
        st.error(f"Nem sikerült írni a Google Sheet-be: {e}")


@st.cache_data(show_spinner = False)
def add_rag1_feedback_to_excel(valasz_rag1, valasz_rag1_visszajelzes, valasz_rag1_helytelen_user_input = None):
    try:
        conn = st.connection("gsheets_kereso", type=GSheetsConnection)
        sheet_name = "DRV_Szabályzat" if selected_tab == "Szabályzat" else (
            "DRV_Jogszabály" if selected_tab == "Jogszabály" else "DRV_Tájékoztató"
        )
        df = conn.read(worksheet=sheet_name, ttl=0)
    except Exception as e:
        st.error(f"Nem sikerült olvasni a Google Sheet-et: {e}")
        return

    current_datetime = datetime.now()

    cols = list(df.columns)
    last_idx = None
    if len(cols) > 1 and not df.empty and cols[1] in df:
        mask = df[cols[1]] == valasz_rag1
        if mask.any():
            last_idx = mask[mask].index[-1]

    def is_empty_value(value):
        return value is None or (isinstance(value, float) and pd.isna(value)) or (isinstance(value, str) and value.strip() == "")

    if last_idx is not None:
        current_feedback = df.at[last_idx, cols[6]] if len(cols) > 6 else None
        if is_empty_value(current_feedback):
            if len(cols) > 6:
                df.at[last_idx, cols[6]] = valasz_rag1_visszajelzes
            if len(cols) > 7:
                df.at[last_idx, cols[7]] = valasz_rag1_helytelen_user_input
            if len(cols) > 10:
                df.at[last_idx, cols[10]] = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if len(cols) > 11:
                df.at[last_idx, cols[11]] = st.session_state.get('username', "")
        else:
            new_row = {c: "" for c in cols}
            for i in range(min(6, len(cols))):
                new_row[cols[i]] = df.at[last_idx, cols[i]]
            if len(cols) > 6:
                new_row[cols[6]] = valasz_rag1_visszajelzes
            if len(cols) > 7:
                new_row[cols[7]] = valasz_rag1_helytelen_user_input
            if len(cols) > 10:
                new_row[cols[10]] = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if len(cols) > 11:
                new_row[cols[11]] = st.session_state.get('username', "")
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        try:
            conn.update(worksheet=sheet_name, data=df)
            print("Felhasználói visszajelzés lementve")
        except Exception as e:
            st.error(f"Nem sikerült írni a Google Sheet-be: {e}")

@st.cache_data(show_spinner = False)
def add_rag2_feedback_to_excel(valasz_rag2, valasz_rag2_visszajelzes, valasz_rag2_helytelen_user_input = None):
    try:
        conn = st.connection("gsheets_kereso", type=GSheetsConnection)
        if valasz_rag2 == st.session_state.get('valasz_rag2_szabalyzat'):
            sheet_name = "DRV_Szabályzat"
        elif valasz_rag2 == st.session_state.get('valasz_rag2_jogszabaly'):
            sheet_name = "DRV_Jogszabály"
        else:
            sheet_name = "DRV_Tájékoztató"
        df = conn.read(worksheet=sheet_name, ttl=0)
    except Exception as e:
        st.error(f"Nem sikerült olvasni a Google Sheet-et: {e}")
        return

    current_datetime = datetime.now()

    cols = list(df.columns)
    last_idx = None
    if len(cols) > 2 and not df.empty and cols[2] in df:
        mask = df[cols[2]] == valasz_rag2
        if mask.any():
            last_idx = mask[mask].index[-1]

    def is_empty_value(value):
        return value is None or (isinstance(value, float) and pd.isna(value)) or (isinstance(value, str) and value.strip() == "")

    if last_idx is not None:
        current_feedback = df.at[last_idx, cols[8]] if len(cols) > 8 else None
        if is_empty_value(current_feedback):
            if len(cols) > 8:
                df.at[last_idx, cols[8]] = valasz_rag2_visszajelzes
            if len(cols) > 9:
                df.at[last_idx, cols[9]] = valasz_rag2_helytelen_user_input
            if len(cols) > 10:
                df.at[last_idx, cols[10]] = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if len(cols) > 11:
                df.at[last_idx, cols[11]] = st.session_state.get('username', "")
        else:
            new_row = {c: "" for c in cols}
            for i in range(min(8, len(cols))):
                new_row[cols[i]] = df.at[last_idx, cols[i]]
            if len(cols) > 8:
                new_row[cols[8]] = valasz_rag2_visszajelzes
            if len(cols) > 9:
                new_row[cols[9]] = valasz_rag2_helytelen_user_input
            if len(cols) > 10:
                new_row[cols[10]] = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
            if len(cols) > 11:
                new_row[cols[11]] = st.session_state.get('username', "")
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        try:
            conn.update(worksheet=sheet_name, data=df)
            print("Felhasználói visszajelzés lementve")
        except Exception as e:
            st.error(f"Nem sikerült írni a Google Sheet-be: {e}")



def disable_feedback_button1_szabalyzat():
    st.session_state['feedback_button1_pressed_szabalyzat'] = True
def disable_feedback_button2_szabalyzat():
    st.session_state['feedback_button2_pressed_szabalyzat'] = True   
def disable_feedback_button1_jogszabaly():
    st.session_state['feedback_button1_pressed_jogszabaly'] = True   
def disable_feedback_button2_jogszabaly():
    st.session_state['feedback_button2_pressed_jogszabaly'] = True
def disable_feedback_button1_tajekoztato():
    st.session_state['feedback_button1_pressed_tajekoztato'] = True   
def disable_feedback_button2_tajekoztato():
    st.session_state['feedback_button2_pressed_tajekoztato'] = True  

@st.dialog(title="Visszajelzés", width="large")
@st.fragment
def user_feedback_on_wrong_rag1_answer(kerdes):
    st.write("Ha tudod a helyes választ, kérlek add meg")
    valasz_rag1_helytelen_user_input = st.text_area(f"Helyes válasz az alábbi keresésre: {kerdes}", height=400)
    if st.button("Küldés"):
        st.session_state['user_feedback_on_wrong_rag1_answer'] = valasz_rag1_helytelen_user_input
        st.session_state['user_feedback_on_wrong_rag1_answer_given'] = True
        st.rerun()

@st.dialog(title="Visszajelzés", width="large")
@st.fragment
def user_feedback_on_wrong_rag2_answer(kerdes):
    st.write("Ha tudod a helyes választ, kérlek add meg")
    valasz_rag2_helytelen_user_input = st.text_area(f"Helyes válasz az alábbi keresésre: {kerdes}", height=400)
    if st.button("Küldés"):
        st.session_state['user_feedback_on_wrong_rag2_answer'] = valasz_rag2_helytelen_user_input
        st.session_state['user_feedback_on_wrong_rag2_answer_given'] = True
        st.rerun()




@st.fragment
def rag_feedback(key):    
    # --------------- RAG1 -----------------
    # ---- Szabályzat ----
    with st.container():

        if 'selected_rag1' not in st.session_state:
            st.session_state['selected_rag1'] = None        
        if 'sentiment_mapping_rag1' not in st.session_state:
            st.session_state['sentiment_mapping_rag1'] = None
        if 'feedback_button1_pressed_szabalyzat' not in st.session_state:
            st.session_state['feedback_button1_pressed_szabalyzat'] = False
            


        if key == "feedback_rag1_szabalyzat":  
            st.session_state['sentiment_mapping_rag1'] = [":material/thumb_down:", ":material/thumb_up:", None]
            st.session_state['selected_rag1'] = None
            st.session_state['selected_rag1'] = st.feedback(options="thumbs",
                                   key=key,
##                                   disabled=st.session_state['feedback_button1_pressed_szabalyzat'],
                                   on_change=disable_feedback_button1_szabalyzat)

            if st.session_state['selected_rag1'] is not None and st.session_state['feedback_button1_pressed_szabalyzat'] == True:
                if st.session_state['sentiment_mapping_rag1'][st.session_state['selected_rag1']] == ":material/thumb_up:":
                    st.caption(f"Helyes válasz")
                    st.session_state['valasz_rag1_visszajelzes_szabalyzat'] = "helyes"
                    add_rag1_feedback_to_excel(valasz_rag1= st.session_state['valasz_rag1_szabalyzat'],
                                               valasz_rag1_visszajelzes = st.session_state['valasz_rag1_visszajelzes_szabalyzat'])

                if st.session_state['sentiment_mapping_rag1'][st.session_state['selected_rag1']] == ":material/thumb_down:":
                    st.caption(f"Helytelen válasz")
                    st.session_state['valasz_rag1_visszajelzes_szabalyzat'] = "helytelen"
                    if st.session_state['user_feedback_on_wrong_rag1_answer_given'] == False:
                        user_feedback_on_wrong_rag1_answer(st.session_state['kerdes_szabalyzat'])
    ##                    return
                    add_rag1_feedback_to_excel(valasz_rag1 = st.session_state['valasz_rag1_szabalyzat'],
                                               valasz_rag1_visszajelzes = st.session_state['valasz_rag1_visszajelzes_szabalyzat'],
                                               valasz_rag1_helytelen_user_input = st.session_state['user_feedback_on_wrong_rag1_answer'])

        # ---- Jogszabály ----
        if key == "feedback_rag1_jogszabaly":  
            sentiment_mapping_rag1 = [":material/thumb_down:", ":material/thumb_up:"]
            selected_rag1 = st.feedback(options="thumbs",
                                   key=key,
##                                   disabled=st.session_state['feedback_button1_pressed_jogszabaly'],
                                   on_change=disable_feedback_button1_jogszabaly)          
            if selected_rag1 is not None:
                if sentiment_mapping_rag1[selected_rag1] == ":material/thumb_up:":
                    st.caption(f"Helyes válasz")
                    st.session_state['valasz_rag1_visszajelzes_jogszabaly'] = "helyes"
                    add_rag1_feedback_to_excel(valasz_rag1= st.session_state['valasz_rag1_jogszabaly'],
                                               valasz_rag1_visszajelzes = st.session_state['valasz_rag1_visszajelzes_jogszabaly'])

                if sentiment_mapping_rag1[selected_rag1] == ":material/thumb_down:":
                    st.caption(f"Helytelen válasz")
                    st.session_state['valasz_rag1_visszajelzes_jogszabaly'] = "helytelen"
                    if st.session_state['user_feedback_on_wrong_rag1_answer_given'] == False:
                        user_feedback_on_wrong_rag1_answer(st.session_state['kerdes_jogszabaly'])
                        return
                    add_rag1_feedback_to_excel(valasz_rag1 = st.session_state['valasz_rag1_jogszabaly'],
                                               valasz_rag1_visszajelzes = st.session_state['valasz_rag1_visszajelzes_jogszabaly'],
                                               valasz_rag1_helytelen_user_input = st.session_state['user_feedback_on_wrong_rag1_answer'])

        # ---- Tájékoztató ----
        if key == "feedback_rag1_tajekoztato":  
            sentiment_mapping_rag1 = [":material/thumb_down:", ":material/thumb_up:"]
            selected_rag1 = st.feedback(options="thumbs",
                                   key=key,)
##                                   disabled=st.session_state['feedback_button1_pressed_tajekoztato'],
##                                   on_change=disable_feedback_button1_tajekoztato)          
            if selected_rag1 is not None:
                if sentiment_mapping_rag1[selected_rag1] == ":material/thumb_up:":
                    st.caption(f"Helyes válasz")
                    st.session_state['valasz_rag1_visszajelzes_tajekoztato'] = "helyes"
                    add_rag1_feedback_to_excel(valasz_rag1= st.session_state['valasz_rag1_tajekoztato'],
                                               valasz_rag1_visszajelzes = st.session_state['valasz_rag1_visszajelzes_tajekoztato'])

                if sentiment_mapping_rag1[selected_rag1] == ":material/thumb_down:":
                    st.caption(f"Helytelen válasz")
                    st.session_state['valasz_rag1_visszajelzes_tajekoztato'] = "helytelen"
                    if st.session_state['user_feedback_on_wrong_rag1_answer_given'] == False:
                        user_feedback_on_wrong_rag1_answer(st.session_state['kerdes_tajekoztato'])
                        return
                    add_rag1_feedback_to_excel(valasz_rag1 = st.session_state['valasz_rag1_tajekoztato'],
                                               valasz_rag1_visszajelzes = st.session_state['valasz_rag1_visszajelzes_tajekoztato'],
                                               valasz_rag1_helytelen_user_input = st.session_state['user_feedback_on_wrong_rag1_answer'])


        # --------------- RAG2 -----------------
        # ---- Szabályzat ----
        if key == "feedback_rag2_szabalyzat": 
            sentiment_mapping_rag2 = [":material/thumb_down:", ":material/thumb_up:"]
            selected_rag2 = st.feedback(options="thumbs",
                                   key=key,
##                                   disabled=st.session_state['feedback_button2_pressed_szabalyzat'],
                                   on_change=disable_feedback_button2_szabalyzat)        
            if selected_rag2 is not None:
                if sentiment_mapping_rag2[selected_rag2] == ":material/thumb_up:":
                    st.caption(f"Helyes válasz")
                    st.session_state['valasz_rag2_visszajelzes_szabalyzat'] = "helyes"
                    add_rag2_feedback_to_excel(valasz_rag2= st.session_state['valasz_rag2_szabalyzat'],
                                               valasz_rag2_visszajelzes = st.session_state['valasz_rag2_visszajelzes_szabalyzat'])

                if sentiment_mapping_rag2[selected_rag2] == ":material/thumb_down:":
                    st.caption(f"Helytelen válasz")
                    st.session_state['valasz_rag2_visszajelzes_szabalyzat'] = "helytelen"
                    if st.session_state['user_feedback_on_wrong_rag2_answer_given'] == False:
                        user_feedback_on_wrong_rag2_answer(st.session_state['kerdes_szabalyzat'])
                        return
                    add_rag2_feedback_to_excel(valasz_rag2 = st.session_state['valasz_rag2_szabalyzat'],
                                               valasz_rag2_visszajelzes = st.session_state['valasz_rag2_visszajelzes_szabalyzat'],
                                               valasz_rag2_helytelen_user_input = st.session_state['user_feedback_on_wrong_rag2_answer'])
                    
        # ---- Jogszabály ----
        if key == "feedback_rag2_jogszabaly": 
            sentiment_mapping_rag2 = [":material/thumb_down:", ":material/thumb_up:"]
            selected_rag2 = st.feedback(options="thumbs",
                                   key=key,
##                                   disabled=st.session_state['feedback_button2_pressed_jogszabaly'],
                                   on_change=disable_feedback_button2_jogszabaly)        
            if selected_rag2 is not None:
                if sentiment_mapping_rag2[selected_rag2] == ":material/thumb_up:":
                    st.caption(f"Helyes válasz")
                    st.session_state['valasz_rag2_visszajelzes_jogszabaly'] = "helyes"
                    add_rag2_feedback_to_excel(valasz_rag2= st.session_state['valasz_rag2_jogszabaly'],
                                               valasz_rag2_visszajelzes = st.session_state['valasz_rag2_visszajelzes_jogszabaly'])

                if sentiment_mapping_rag2[selected_rag2] == ":material/thumb_down:":
                    st.caption(f"Helytelen válasz")
                    st.session_state['valasz_rag2_visszajelzes_jogszabaly'] = "helytelen"
                    if st.session_state['user_feedback_on_wrong_rag2_answer_given'] == False:
                        user_feedback_on_wrong_rag2_answer(st.session_state['kerdes_jogszabaly'])
                        return
                    add_rag2_feedback_to_excel(valasz_rag2 = st.session_state['valasz_rag2_jogszabaly'],
                                               valasz_rag2_visszajelzes = st.session_state['valasz_rag2_visszajelzes_jogszabaly'],
                                               valasz_rag2_helytelen_user_input = st.session_state['user_feedback_on_wrong_rag2_answer'])    
        
        # ---- Tájékoztató ----
        if key == "feedback_rag2_tajekoztato": 
            sentiment_mapping_rag2 = [":material/thumb_down:", ":material/thumb_up:"]
            selected_rag2 = st.feedback(options="thumbs",
                                   key=key,
##                                   disabled=st.session_state['feedback_button2_pressed_tajekoztato'],
                                   on_change=disable_feedback_button2_tajekoztato)        
            if selected_rag2 is not None:
                if sentiment_mapping_rag2[selected_rag2] == ":material/thumb_up:":
                    st.caption(f"Helyes válasz")
                    st.session_state['valasz_rag2_visszajelzes_tajekoztato'] = "helyes"
                    add_rag2_feedback_to_excel(valasz_rag2= st.session_state['valasz_rag2_tajekoztato'],
                                               valasz_rag2_visszajelzes = st.session_state['valasz_rag2_visszajelzes_tajekoztato'])

                if sentiment_mapping_rag2[selected_rag2] == ":material/thumb_down:":
                    st.caption(f"Helytelen válasz")
                    st.session_state['valasz_rag2_visszajelzes_tajekoztato'] = "helytelen"
                    if st.session_state['user_feedback_on_wrong_rag2_answer_given'] == False:
                        user_feedback_on_wrong_rag2_answer(st.session_state['kerdes_tajekoztato'])
                        return
                    add_rag2_feedback_to_excel(valasz_rag2 = st.session_state['valasz_rag2_tajekoztato'],
                                               valasz_rag2_visszajelzes = st.session_state['valasz_rag2_visszajelzes_tajekoztato'],
                                               valasz_rag2_helytelen_user_input = st.session_state['user_feedback_on_wrong_rag2_answer'])    
@st.cache_data(show_spinner = False)
def search_count_save(username, kereses_button_pressed):
    try:
        conn = st.connection("gsheets_keresesek_szama", type=GSheetsConnection)
        import os as _os
        ws_name = "DRV"
        df = conn.read(worksheet=ws_name, ttl=0)
    except Exception as e:
        st.error(f"Nem sikerült olvasni a Google Sheet-et: {e}")
        return

    cols = list(df.columns) if isinstance(df, pd.DataFrame) else []
    if len(cols) < 4:
        st.error("A Google Sheet szerkezete nem megfelelő (legalább 4 oszlop szükséges).")
        return

    last_idx = None
    if not df.empty:
        mask = df[cols[0]] == username
        if mask.any():
            last_idx = mask[mask].index[-1]

    tab_to_colidx = {
        "Szabályzat": 1,
        "Jogszabály": 2,
        "Tájékoztató": 3,
    }
    col_idx = tab_to_colidx.get(selected_tab)
    if col_idx is None or col_idx >= len(cols):
        st.error("Ismeretlen fül a számlálóhoz vagy hibás oszlop index.")
        return

    if last_idx is not None:
        current = df.at[last_idx, cols[col_idx]]
        try:
            current_val = int(current) if current not in (None, "") and not (isinstance(current, float) and pd.isna(current)) else 0
        except Exception:
            current_val = 0
        df.at[last_idx, cols[col_idx]] = current_val + 1
    else:
        new_row = {c: 0 for c in cols}
        new_row[cols[0]] = username
        new_row[cols[1]] = 0
        new_row[cols[2]] = 0
        new_row[cols[3]] = 0
        new_row[cols[col_idx]] = kereses_button_pressed
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    try:
        conn.update(worksheet=ws_name, data=df)
    except Exception as e:
        st.error(f"Nem sikerült írni a Google Sheet-be: {e}")
# ------------------------------- Streamlit GUI -------------------------------
# Insert an anchor at the top of the page
st.markdown('<a id="top"></a>', unsafe_allow_html=True)

col1, col2, col3 = st.columns([1,10,3])


# Inject CSS for smooth scrolling, fixed positioning, button styling, and a custom tooltip with a 2s delay
st.markdown(
    """
    <style>
    html {
        scroll-behavior: smooth;
    }
    .fixed-button {
        position: fixed;
        bottom: 20px;
        right: 80px;
        z-index: 999;
    }
    .fixed-button a {
        text-decoration: none;
        position: relative; /* Establish positioning context for the tooltip */
    }
    .circle-button {
        width: 40px;
        height: 40px;
        background-color: #0E1117;
        border: 1px solid #6A6C7B;
        border-radius: 50%;
        color: #6A6C7B;
        font-size: 36px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
        transition: border-color 0.2s, color 0.2s;
    }
    /* Move the arrow upward a bit inside the button */
    .circle-button span {
        position: relative;
        top: -2px;
    }
    /* On hover, change both border and arrow color to #81CFF4 */
    .circle-button:hover {
        border-color: #81CFF4;
    }
    .circle-button:hover span {
        color: #81CFF4;
    }
    
    /* Custom tooltip styling */
    .tooltip {
        opacity: 0;
        visibility: hidden;
        position: absolute;
        bottom: 50px; /* Positioned above the button */
        right: 0;
        background-color: #0E1117;
        color: #FAFAFA;
        text-align: center;
        border: 1px solid #262730;
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 12px;
        white-space: nowrap;
    }
    /* When hovering, start an animation that waits 0.4s then shows the tooltip instantly */
    .fixed-button a:hover .tooltip {
        animation: showTooltip 0s 0.4s forwards;
    }
    /* Define keyframes that set the tooltip to visible */
    @keyframes showTooltip {
        to { opacity: 1; visibility: visible; }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Create the fixed circular button with the upward arrow and custom tooltip
st.markdown(
    """
    <div class="fixed-button">
        <a href="#top">
            <button class="circle-button"><span>&#8593;</span></button>
            <div class="tooltip">Vissza az oldal tetejére</div>
        </a>
    </div>
    """,
    unsafe_allow_html=True
)



    


###Ez végre megoldja a bugot, hogy megmarad az előző keresés az újnál.
##placeholder_reset = st.empty()
##if 'reset' not in st.session_state:
##    st.session_state['reset'] = False
##with placeholder_reset:
##    if st.session_state['reset'] == True:
##        st.header("Új keresés indítása folyamatban...")
####        time.sleep(0.1)
##        st.session_state['reset'] = False
##        st.empty()
####        st.rerun()
##    else:
##        pass     


with col2:
    
    ### Title of the web app
    st.markdown(
        "<h1 style='text-align: center;'>DRV Zrt. Információ Kereső</h1>",
        unsafe_allow_html=True
    )
                       
    selected_tab = st.radio("Válaszd ki milyen típusú dokumentumokban akarsz keresni.",
                            ["Szabályzat", "Jogszabály"], #"Tájékoztató"
                            horizontal=True,
                            help="Egyelőre csak az alábbi publikus dokumentumok között.",
                            captions=["Üzletszabályzat, Árnyilvántartás", "Víziközmű törvény", "Általános bekötési tájékoztatók"])

    ##----- Szabályzat -----
    def initialize_session_states_szabalyzat():
        if 'kerdes_szabalyzat' not in st.session_state:
            st.session_state['kerdes_szabalyzat'] = ""
        if 'kereses_button_szabalyzat' not in st.session_state:
            st.session_state['kereses_button_szabalyzat'] = 0
        if 'kereses_button_szabalyzat_pressed' not in st.session_state:
            st.session_state['kereses_button_szabalyzat_pressed'] = False

            
        if 'kerdes_szabalyzat_fragment' not in st.session_state:
            st.session_state['kerdes_szabalyzat_fragment'] = ""
        if 'feedback_button1_pressed_szabalyzat' not in st.session_state:
            st.session_state['feedback_button1_pressed_szabalyzat'] = False
        if 'feedback_button2_pressed_szabalyzat' not in st.session_state:
            st.session_state['feedback_button2_pressed_szabalyzat'] = False
        if 'user_feedback_on_wrong_rag1_answer_given' not in st.session_state:
            st.session_state['user_feedback_on_wrong_rag1_answer_given'] = False        
        if 'user_feedback_on_wrong_rag1_answer' not in st.session_state:
            st.session_state['user_feedback_on_wrong_rag1_answer'] = "" 
        if 'user_feedback_on_wrong_rag2_answer_given' not in st.session_state:
            st.session_state['user_feedback_on_wrong_rag2_answer_given'] = False        
        if 'user_feedback_on_wrong_rag2_answer' not in st.session_state:
            st.session_state['user_feedback_on_wrong_rag2_answer'] = ""

        if 'kereses_popular_button_szabalyzat_pressed' not in st.session_state:
            st.session_state['kereses_popular_button_szabalyzat_pressed'] = False
        if 'need_to_switch' not in st.session_state:
            st.session_state['need_to_switch'] = True

            
        if 'search_complete_toc_szabalyzat' not in st.session_state:
            st.session_state['search_complete_toc_szabalyzat'] = False
        if 'valaszok_szabalyzat' not in st.session_state:
            st.session_state['valaszok_toc_szabalyzat'] = []
        if 'nevek_szabalyzat' not in st.session_state:
            st.session_state['nevek_toc_szabalyzat'] = []
        if 'oldalszamok_szabalyzat' not in st.session_state:
            st.session_state['oldalszamok_toc_szabalyzat'] = []
        if 'eleresi_helyek_szabalyzat' not in st.session_state:
            st.session_state['eleresi_helyek_toc_szabalyzat'] = []
        if 'ids_szabalyzat' not in st.session_state:
            st.session_state['ids_toc_szabalyzat'] = []

        if 'search_complete_szabalyzat' not in st.session_state:
            st.session_state['search_complete_szabalyzat'] = False
        if 'valaszok_szabalyzat' not in st.session_state:
            st.session_state['valaszok_szabalyzat'] = []
        if 'nevek_szabalyzat' not in st.session_state:
            st.session_state['nevek_szabalyzat'] = []
        if 'oldalszamok_szabalyzat' not in st.session_state:
            st.session_state['oldalszamok_szabalyzat'] = []
        if 'eleresi_helyek_szabalyzat' not in st.session_state:
            st.session_state['eleresi_helyek_szabalyzat'] = []
        if 'ids_szabalyzat' not in st.session_state:
            st.session_state['ids_szabalyzat'] = []
            
        if 'valasz_rag1_szabalyzat' not in st.session_state:
            st.session_state['valasz_rag1_szabalyzat'] = ""
        if 'valasz_rag2_szabalyzat' not in st.session_state:
            st.session_state['valasz_rag2_szabalyzat'] = ""
        if 'model_rag1_szabalyzat' not in st.session_state:
            st.session_state['model_rag1_szabalyzat'] = ""        
        if 'valasz_rag1_visszajelzes_szabalyzat' not in st.session_state:
            st.session_state['valasz_rag1_visszajelzes_szabalyzat'] = ""
        if 'valasz_rag1_helytelen_user_input_szabalyzat' not in st.session_state:
            st.session_state['valasz_rag1_helytelen_user_input_szabalyzat'] = ""   
        if 'valasz_rag2_visszajelzes_szabalyzat' not in st.session_state:
            st.session_state['valasz_rag2_visszajelzes_szabalyzat'] = ""
        if 'valasz_rag2_helytelen_user_input_szabalyzat' not in st.session_state:
            st.session_state['valasz_rag2_helytelen_user_input_szabalyzat'] = ""

        if 'kereses_done_szabalyzat' not in st.session_state:
            st.session_state['kereses_done_szabalyzat'] = False




    ##----- Jogszabály -----

    def initialize_session_states_jogszabaly():
        if 'kereses_button_jogszabaly_pressed' not in st.session_state:
            st.session_state['kereses_button_jogszabaly_pressed'] = False        
        if 'kerdes_jogszabaly' not in st.session_state:
            st.session_state['kerdes_jogszabaly'] = ""
        if 'kereses_button_jogszabaly' not in st.session_state:
            st.session_state['kereses_button_jogszabaly'] = 0
        if 'kerdes_jogszabaly_fragment' not in st.session_state:
            st.session_state['kerdes_jogszabaly_fragment'] = ""
        if 'feedback_button1_pressed_jogszabaly' not in st.session_state:
            st.session_state['feedback_button1_pressed_jogszabaly'] = False
        if 'feedback_button2_pressed_jogszabaly' not in st.session_state:
            st.session_state['feedback_button2_pressed_jogszabaly'] = False
        if 'user_feedback_on_wrong_rag1_answer_given' not in st.session_state:
            st.session_state['user_feedback_on_wrong_rag1_answer_given'] = False        
        if 'user_feedback_on_wrong_rag1_answer' not in st.session_state:
            st.session_state['user_feedback_on_wrong_rag1_answer'] = "" 
        if 'user_feedback_on_wrong_rag2_answer_given' not in st.session_state:
            st.session_state['user_feedback_on_wrong_rag2_answer_given'] = False        
        if 'user_feedback_on_wrong_rag2_answer' not in st.session_state:
            st.session_state['user_feedback_on_wrong_rag2_answer'] = "" 

        if 'kereses_popular_button_jogszabaly_pressed' not in st.session_state:
            st.session_state['kereses_popular_button_jogszabaly_pressed'] = False
        if 'need_to_switch' not in st.session_state:
            st.session_state['need_to_switch'] = True
            
        if 'search_complete_toc_jogszabaly' not in st.session_state:
            st.session_state['search_complete_toc_jogszabaly'] = False
        if 'valaszok_jogszabaly' not in st.session_state:
            st.session_state['valaszok_toc_jogszabaly'] = []
        if 'nevek_jogszabaly' not in st.session_state:
            st.session_state['nevek_toc_jogszabaly'] = []
        if 'oldalszamok_jogszabaly' not in st.session_state:
            st.session_state['oldalszamok_toc_jogszabaly'] = []
        if 'eleresi_helyek_jogszabaly' not in st.session_state:
            st.session_state['eleresi_helyek_toc_jogszabaly'] = []
        if 'ids_jogszabaly' not in st.session_state:
            st.session_state['ids_toc_jogszabaly'] = []

        if 'search_complete_jogszabaly' not in st.session_state:
            st.session_state['search_complete_jogszabaly'] = False
        if 'valaszok_jogszabaly' not in st.session_state:
            st.session_state['valaszok_jogszabaly'] = []
        if 'nevek_jogszabaly' not in st.session_state:
            st.session_state['nevek_jogszabaly'] = []
        if 'oldalszamok_jogszabaly' not in st.session_state:
            st.session_state['oldalszamok_jogszabaly'] = []
        if 'eleresi_helyek_jogszabaly' not in st.session_state:
            st.session_state['eleresi_helyek_jogszabaly'] = []
        if 'ids_jogszabaly' not in st.session_state:
            st.session_state['ids_jogszabaly'] = []
            
        if 'valasz_rag1_jogszabaly' not in st.session_state:
            st.session_state['valasz_rag1_jogszabaly'] = ""
        if 'valasz_rag2_jogszabaly' not in st.session_state:
            st.session_state['valasz_rag2_jogszabaly'] = ""
        if 'model_rag1_jogszabaly' not in st.session_state:
            st.session_state['model_rag1_jogszabaly'] = ""        
        if 'valasz_rag1_visszajelzes_jogszabaly' not in st.session_state:
            st.session_state['valasz_rag1_visszajelzes_jogszabaly'] = ""
        if 'valasz_rag1_helytelen_user_input_jogszabaly' not in st.session_state:
            st.session_state['valasz_rag1_helytelen_user_input_jogszabaly'] = ""   
        if 'valasz_rag2_visszajelzes_jogszabaly' not in st.session_state:
            st.session_state['valasz_rag2_visszajelzes_jogszabaly'] = ""
        if 'valasz_rag2_helytelen_user_input_jogszabaly' not in st.session_state:
            st.session_state['valasz_rag2_helytelen_user_input_jogszabaly'] = ""   

        if 'kereses_done_jogszabaly' not in st.session_state:
            st.session_state['kereses_done_jogszabaly'] = False

    ##----- Tájékoztató -----

    def initialize_session_states_tajekoztato():
        if 'kereses_button_tajekoztato_pressed' not in st.session_state:
            st.session_state['kereses_button_tajekoztato_pressed'] = False        
        if 'kerdes_tajekoztato' not in st.session_state:
            st.session_state['kerdes_tajekoztato'] = ""
        if 'kereses_button_tajekoztato' not in st.session_state:
            st.session_state['kereses_button_tajekoztato'] = 0 
        if 'kerdes_tajekoztato_fragment' not in st.session_state:
            st.session_state['kerdes_tajekoztato_fragment'] = ""
        if 'feedback_button1_pressed_tajekoztato' not in st.session_state:
            st.session_state['feedback_button1_pressed_tajekoztato'] = False
        if 'feedback_button2_pressed_tajekoztato' not in st.session_state:
            st.session_state['feedback_button2_pressed_tajekoztato'] = False
        if 'user_feedback_on_wrong_rag1_answer_given' not in st.session_state:
            st.session_state['user_feedback_on_wrong_rag1_answer_given'] = False        
        if 'user_feedback_on_wrong_rag1_answer' not in st.session_state:
            st.session_state['user_feedback_on_wrong_rag1_answer'] = "" 
        if 'user_feedback_on_wrong_rag2_answer_given' not in st.session_state:
            st.session_state['user_feedback_on_wrong_rag2_answer_given'] = False        
        if 'user_feedback_on_wrong_rag2_answer' not in st.session_state:
            st.session_state['user_feedback_on_wrong_rag2_answer'] = "" 

        if 'kereses_popular_button_tajekoztato_pressed' not in st.session_state:
            st.session_state['kereses_popular_button_tajekoztato_pressed'] = False
        if 'need_to_switch' not in st.session_state:
            st.session_state['need_to_switch'] = True

##Ha lesz több doksi, tartalomjegyzékkel, be lehet majd kapcsolni            
##        if 'search_complete_toc_tajekoztato' not in st.session_state:
##            st.session_state['search_complete_toc_tajekoztato'] = False
##        if 'valaszok_tajekoztato' not in st.session_state:
##            st.session_state['valaszok_toc_tajekoztato'] = []
##        if 'nevek_tajekoztato' not in st.session_state:
##            st.session_state['nevek_toc_tajekoztato'] = []
##        if 'oldalszamok_tajekoztato' not in st.session_state:
##            st.session_state['oldalszamok_toc_tajekoztato'] = []
##        if 'eleresi_helyek_tajekoztato' not in st.session_state:
##            st.session_state['eleresi_helyek_toc_tajekoztato'] = []
##        if 'ids_tajekoztato' not in st.session_state:
##            st.session_state['ids_toc_tajekoztato'] = []

        if 'search_complete_tajekoztato' not in st.session_state:
            st.session_state['search_complete_tajekoztato'] = False
        if 'valaszok_tajekoztato' not in st.session_state:
            st.session_state['valaszok_tajekoztato'] = []
        if 'nevek_tajekoztato' not in st.session_state:
            st.session_state['nevek_tajekoztato'] = []
        if 'oldalszamok_tajekoztato' not in st.session_state:
            st.session_state['oldalszamok_tajekoztato'] = []
        if 'eleresi_helyek_tajekoztato' not in st.session_state:
            st.session_state['eleresi_helyek_tajekoztato'] = []
        if 'ids_tajekoztato' not in st.session_state:
            st.session_state['ids_tajekoztato'] = []
            
        if 'valasz_rag1_tajekoztato' not in st.session_state:
            st.session_state['valasz_rag1_tajekoztato'] = ""
        if 'valasz_rag2_tajekoztato' not in st.session_state:
            st.session_state['valasz_rag2_tajekoztato'] = ""
        if 'model_rag1_tajekoztato' not in st.session_state:
            st.session_state['model_rag1_tajekoztato'] = ""        
        if 'valasz_rag1_visszajelzes_tajekoztato' not in st.session_state:
            st.session_state['valasz_rag1_visszajelzes_tajekoztato'] = ""
        if 'valasz_rag1_helytelen_user_input_tajekoztato' not in st.session_state:
            st.session_state['valasz_rag1_helytelen_user_input_tajekoztato'] = ""   
        if 'valasz_rag2_visszajelzes_tajekoztato' not in st.session_state:
            st.session_state['valasz_rag2_visszajelzes_tajekoztato'] = ""
        if 'valasz_rag2_helytelen_user_input_tajekoztato' not in st.session_state:
            st.session_state['valasz_rag2_helytelen_user_input_tajekoztato'] = ""   

        if 'rag_search_running_tajekoztato' not in st.session_state:
            st.session_state['rag_search_running_tajekoztato'] = False
        if 'rag_search_running2_tajekoztato' not in st.session_state:
            st.session_state['rag_search_running2_tajekoztato'] = False

        if 'kereses_done_tajekoztato' not in st.session_state:
            st.session_state['kereses_done_tajekoztato'] = False




    ##------------------------ Szabályzat ------------------------

    if selected_tab == "Szabályzat":
        content = st.container()
       
        with content:
##            content.empty()

            def kereses_button_szabalyzat():
##                st.empty()
##                content.empty()
                print("--------------------------------------------------------------------------")
            ##    print(f'Dátum: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}') #Ez valamiért kinyírja a programot. Mindegy, excel rögzít Összefoglalásnál dátumot is.
                print(f"Felhasználó: {st.session_state['username']}")
                st.session_state['kereses_button_szabalyzat_pressed'] = True
                st.session_state['kereses_button_szabalyzat'] += 1
                st.session_state['feedback_button1_pressed_szabalyzat'] = False
                st.session_state['feedback_button2_pressed_szabalyzat'] = False
                st.session_state['user_feedback_on_wrong_rag1_answer_given'] = False
                st.session_state['user_feedback_on_wrong_rag2_answer_given'] = False
                st.session_state['rag1_done_szabalyzat'] = False
                st.session_state['rag2_done_szabalyzat'] = False
                search_count_save(
                             username = st.session_state['username'],
                             kereses_button_pressed = st.session_state['kereses_button_szabalyzat'])
            
            if 'kereses_button_szabalyzat' not in st.session_state:
                initialize_session_states_szabalyzat()
            if 'kereses_popular_button_szabalyzat_pressed' not in st.session_state:
                initialize_session_states_szabalyzat()
            
            # Function to find matches and store them in session state
            def find_and_store_toc_results_szabalyzat(user_input, collection_name):
                organized_matches_toc, valaszok_toc, eleresi_helyek_toc, ids_toc, oldalszamok_toc, nevek_toc = find_matches(user_input, keresesek_szama, collection_name="DRV_tartalomjegyzek_szabalyzat")
                # Store results in session state
                st.session_state['valaszok_toc_szabalyzat'] = valaszok_toc
                st.session_state['nevek_toc_szabalyzat'] = nevek_toc
                st.session_state['oldalszamok_toc_szabalyzat'] = oldalszamok_toc
                st.session_state['eleresi_helyek_toc_szabalyzat'] = eleresi_helyek_toc
                st.session_state['ids_toc_szabalyzat'] = ids_toc
                st.session_state['search_complete_toc_szabalyzat'] = True  # Mark search as complete
        ##            time.sleep(2)


            def display_tartalomjegyzek_szabalyzat():
                with st.container():
##                    st.empty()
                    st.subheader("Tartalomjegyzék találatok:", help=f"A találatra kattintva megnyitja az aktuális dokumentumot, de utána az oldalszámot nekünk kell beírni, hogy odaugorjon.")
                    for i in range(min(5, len(st.session_state['valaszok_toc_szabalyzat'][:5]))):
                ##        print(f"i értéke: {i}")
                ##        print(f"{st.session_state['nevek'][i]}")
                ##        print(f"{st.session_state['valaszok'][i]}")
                ##        print(f"{st.session_state['oldalszamok'][i]}")
                ##        print(f"{st.session_state['eleresi_helyek'][i]}")
                        st.link_button(
                            f"{st.session_state['nevek_toc_szabalyzat'][i]}: {st.session_state['valaszok_toc_szabalyzat'][i]}  . . . . . .  {st.session_state['oldalszamok_toc_szabalyzat'][i]}",
                            help=f'{st.session_state["nevek_toc_szabalyzat"][i]} megnyitása',
                            url = f"{st.session_state['eleresi_helyek_toc_szabalyzat'][i]}",
                            use_container_width=False,
                        )
##                    st.empty()
                    print(f"\nTartalomjegyzék találatok: \n{st.session_state['valaszok_toc_szabalyzat'][:5]}")


            # Function to find matches and store them in session state
            def find_and_store_results_szabalyzat(user_input, collection_name):
                organized_matches, valaszok, eleresi_helyek, ids, oldalszamok, nevek = find_matches(user_input, keresesek_szama, collection_name)
                # Store results in session state
                st.session_state['valaszok_szabalyzat'] = valaszok
                st.session_state['nevek_szabalyzat'] = nevek
                st.session_state['oldalszamok_szabalyzat'] = oldalszamok
                st.session_state['eleresi_helyek_szabalyzat'] = eleresi_helyek
                st.session_state['ids_szabalyzat'] = ids
                st.session_state['search_complete_szabalyzat'] = True  # Mark search as complete
        ##            time.sleep(5)


            def display_valasz_szabalyzat():
                st.divider()
                st.subheader("Pontos találatok a dokumentumokból a megadott válasz ellenőrzéséhez:", help="Független a Tartalomjegyzék találatoktól")
                for idx, (valasz, eleresi_hely, id_, nev, oldalszam) in enumerate(zip(
                        st.session_state['valaszok_szabalyzat'][:5],
                        st.session_state['eleresi_helyek_szabalyzat'][:5],
                        st.session_state['ids_szabalyzat'][:5],
                        st.session_state['nevek_szabalyzat'][:5],
                        st.session_state['oldalszamok_szabalyzat'][:5]), start=1):
                    
                    with st.container():
##                        st.subheader(f'{idx}. Találat az {nev} {oldalszam}. oldalán:') #később odafigyelni a névelőre, ha több doksi is hozzá lesz adva.
                        st.markdown(f"#### {idx}. Találat az [{nev}]({eleresi_hely}) {oldalszam}. oldalán:", unsafe_allow_html=True)
                        st.text_area("label", value=valasz, height=400, key=f'valasz_szabalyzat{idx}', label_visibility="hidden")
##                        st.markdown(f"Elérési hely: {eleresi_hely}", unsafe_allow_html=True)
##                        id_number = int(id_[2:])
                       
                print("\nVálaszok mutatva")
    ##            print(f"\nVálasz 1. találat: \n{st.session_state['valaszok_szabalyzat'][0]}")

            @st.fragment()
            def show_more_szabalyzat():
                if st.button("Mutass többet", use_container_width=True):
                    for idx, (valasz, eleresi_hely, id_, nev, oldalszam) in enumerate(zip(
                            st.session_state['valaszok_szabalyzat'][5:10],
                            st.session_state['eleresi_helyek_szabalyzat'][5:10],
                            st.session_state['ids_szabalyzat'][5:10],
                            st.session_state['nevek_szabalyzat'][5:10],
                            st.session_state['oldalszamok_szabalyzat'][5:10]), start=6):
                            
                        with st.container():
                            st.markdown(f"#### {idx}. Találat az [{nev}]({eleresi_hely}) {oldalszam}. oldalán:", unsafe_allow_html=True)                          
                            st.text_area("label", value=valasz, height=400, key=f'valasz_szabalyzat{idx}', label_visibility="hidden")
##                            id_number = int(id_[2:])
                                            
                    print("\nTovábbi válaszok mutatva")


            def rag_valasz_szabalyzat():

                def rag1_button_disable_szabalyzat():
                    st.session_state['rag1_done_szabalyzat'] = True

                if 'rag1_done_szabalyzat' not in st.session_state:
                    st.session_state['rag1_done_szabalyzat'] = False

                if 'rag2_done_szabalyzat' not in st.session_state:
                    st.session_state['rag2_done_szabalyzat'] = False

    ##                if 'rag_search_running' not in st.session_state:
    ##                    st.session_state.rag_search_running = False
                if 'rag_search_running2' not in st.session_state:
                    st.session_state.rag_search_running2 = False

                if 'kerdes_szabalyzat_keyword_only' not in st.session_state:
                    st.session_state['kerdes_szabalyzat_keyword_only'] = ""

                def stream_data(rag_valasz):
                    st.empty()
                    rag_valasz = f"{rag_valasz}\n\n:blue[Ha pontosabb információt szeretnél megtudni a témáról, vagy további részletekre van szükséged, tedd fel **_konkrét kérdésedet!_**]\n\n *A megadott választ az alábbi gombokkal **értékelheted**.*"
                    for word in rag_valasz.split(" "):
                        yield word + " "
                        time.sleep(0.04)



                st.divider()    
    ##                if st.button('Kattints ide a találatok összefoglalásához, konkrét kérdés esetén annak megválaszolásához',
    ##                             help = "A demo erejéig korlátlan összefoglalás, később limitálva lesz",
    ##                             disabled=st.session_state.rag_search_running,
    ##                             key='rag1_button_szabalyzat',
    ##                             on_click = rag1_button_disable_szabalyzat):
    ##                    st.empty()
                response, token_usage, model = ask_question_with_rag(kerdes = st.session_state['kerdes_szabalyzat'], valaszok = st.session_state['valaszok_szabalyzat'], ids = st.session_state['ids_szabalyzat'], nev = st.session_state['nevek_szabalyzat'], oldalszam = st.session_state['oldalszamok_szabalyzat'])
                koltseg = costs(token_usage, model)
                st.session_state['valasz_rag1_szabalyzat'] = response
                st.session_state['koltseg_rag1_szabalyzat'] = koltseg
                st.session_state['model_rag1_szabalyzat'] = model
                st.session_state['valasz_rag2_szabalyzat'] = "-"
                st.session_state['koltseg_rag2_szabalyzat'] = "-"
                st.session_state['kerdes_szabalyzat_fragment'] = st.session_state['kerdes_szabalyzat']
        
                st.session_state['rag1_done_szabalyzat'] = True
                
                print("\nrag1_szabalyzat lefutott")
            ##        st.write(st.session_state)
                
                if st.session_state['rag1_done_szabalyzat'] == True and st.session_state['kerdes_szabalyzat_fragment'] == st.session_state['kerdes_szabalyzat']: #ez utóbbi azért kell, hogy ha megváltozik a kérdés ne mutassa az előző összefoglalást
                    with st.container():
##                            content.empty()
                        if st.session_state['kereses_popular_button_szabalyzat_pressed'] == True:
                            ## Using simple markdown/write:
                            st.markdown(f"{st.session_state['valasz_rag1_szabalyzat']}\n\n :blue[Ha pontosabb információt szeretnél megtudni a témáról, vagy további részletekre van szükséged, tedd fel **_konkrét kérdésedet!_**]\n\n *A megadott választ az alábbi gombokkal **értékelheted**.*")
                            st.session_state['kereses_done_szabalyzat'] = False
##                    st.empty()
                    with st.container():
##                            content.empty()
                        if st.session_state['kereses_popular_button_szabalyzat_pressed'] == False and st.session_state['kereses_done_szabalyzat'] == False:
                            ## Using streaming (later):
                            st.markdown(f"{st.session_state['valasz_rag1_szabalyzat']}\n\n :blue[Ha pontosabb információt szeretnél megtudni a témáról, vagy további részletekre van szükséged, tedd fel **_konkrét kérdésedet!_**]\n\n *A megadott választ az alábbi gombokkal **értékelheted**.*")
##                            st.write_stream(stream_data(st.session_state['valasz_rag1_szabalyzat']))
                        if st.session_state['kereses_popular_button_szabalyzat_pressed'] == False and st.session_state['kereses_done_szabalyzat'] == True:
                            st.caption(f"{st.session_state['kerdes_szabalyzat']}")
                            st.markdown(f"{st.session_state['valasz_rag1_szabalyzat']}\n\n :blue[Ha pontosabb információt szeretnél megtudni a témáról, vagy további részletekre van szükséged, tedd fel **_konkrét kérdésedet!_**]\n\n *A megadott választ az alábbi gombokkal **értékelheted**.*")
##                            st.markdown(f"Költség: {st.session_state['koltseg_rag1_szabalyzat']} Ft")
                            st.session_state['kereses_done_szabalyzat'] = False
                        store_data_in_excel_szabalyzat(st.session_state['kerdes_szabalyzat'], st.session_state['valasz_rag1_szabalyzat'], st.session_state['valasz_rag2_szabalyzat'],
                                                     st.session_state['koltseg_rag1_szabalyzat'], st.session_state['koltseg_rag2_szabalyzat'], st.session_state['model_rag1_szabalyzat'], st.session_state['username'])
                        rag_feedback(key="feedback_rag1_szabalyzat")
                        st.caption(":red[Fontos:] az összefoglalt válasz lehet pontatlan, akár téves is. A megadott választ minden esetben ellenőrizni kell!")


                if st.session_state['rag1_done_szabalyzat'] == True:

                    @st.fragment()
                    def rag2_szabalyzat_start():

                        def rag2_button_disable_szabalyzat():
                            st.empty() # ez kell!
                            st.session_state['rag2_done_szabalyzat'] = True
                            st.session_state.rag_search_running2 = True
                  
                        if st.button("Újrapróbálkozás a kérdés automatikus átfogalmazásával",
                                     help=f'Bonyolultabb kérdés esetén más módszerrel próbál választ adni. \n\nEgyszerű témánál nem változik a válasz.',
                                     disabled=st.session_state.rag_search_running2,
                                     on_click = rag2_button_disable_szabalyzat,
                                     key = "rag2_button_szabalyzat"):
                            st.empty()
                            st.session_state['kerdes_szabalyzat_keyword_only'] = refactor_question_keyword_only(kerdes = st.session_state['kerdes_szabalyzat']) #Nem jó, a válaszokat kell refactorálni, hogy a rag azokban keresse a választ!!! Most nem fontos, majd fixálni kell. Ez most csak annyit csinál, hogy a fő témára rákeres és megpróbál minden hasznos infot elmondani róla.
                            response, token_usage, model = ask_question_with_rag(kerdes = st.session_state['kerdes_szabalyzat_keyword_only'], valaszok = st.session_state['valaszok_szabalyzat'], ids = st.session_state['ids_szabalyzat'], nev = st.session_state['nevek_szabalyzat'], oldalszam = st.session_state['oldalszamok_szabalyzat'])
                            koltseg = costs(token_usage, model)
                            st.session_state['valasz_rag2_szabalyzat'] = response
                            st.session_state['koltseg_rag2_szabalyzat'] = koltseg
                            st.session_state['model_rag1_szabalyzat'] = model
                            st.session_state['rag2_done_szabalyzat'] = True
                            print("\nrag2_szabalyzat lefutott")

                        if st.session_state['rag2_done_szabalyzat'] == True and st.session_state['kerdes_szabalyzat_fragment'] == st.session_state['kerdes_szabalyzat']: #ez utóbbi azért kell, hogy ha megváltozik a kérdés ne mutassa az előző összefoglalást
                            st.header(f'Alternatív válasz:')
                            st.text_area("rag2_label_szabalyzat",
                                         value=f"{st.session_state['valasz_rag2_szabalyzat']}\n\n:blue[Ha pontosabb információt szeretnél megtudni a témáról, vagy további részletekre van szükséged, tedd fel **_konkrét kérdésedet!_**]\n\n *A megadott választ az alábbi gombokkal **értékelheted**.*",
                                         height=400,
                                         key="valasz_rag2_szabalyzat_text_area",
                                         label_visibility="hidden")
                ##            st.markdown(f"Költség: {st.session_state['koltseg_rag1_szabalyzat']} Ft")
                            store_data_in_excel_szabalyzat(st.session_state['kerdes_szabalyzat'], st.session_state['valasz_rag1_szabalyzat'], st.session_state['valasz_rag2_szabalyzat'],
                                                         st.session_state['koltseg_rag1_szabalyzat'], st.session_state['koltseg_rag2_szabalyzat'], st.session_state['model_rag1_szabalyzat'], st.session_state['username'])
                            rag_feedback(key="feedback_rag2_szabalyzat")
                            st.caption(":red[Fontos:] az összefoglalt válasz lehet pontatlan, akár téves is. A megadott választ minden esetben ellenőrizni kell!")
                            

                        if st.session_state['rag1_done_szabalyzat'] == True and st.session_state['rag2_done_szabalyzat'] == True:
                            st.session_state.rag_search_running2 = False  # Re-enable Button 2 after processing
                            st.session_state.rag_search_running = False   # Re-enable Button 1 after processing
                            st.session_state['rag2_done_szabalyzat'] = False
                            st.error("Nincs több összefoglalt válasz.")

##                    rag2_szabalyzat_start()   #Ezt később lehet érdemes bevezetni valamilyen formában.


            

            with st.form("my_form", border = False):    
                # Text box for user input
                user_input_szabalyzat = st.text_input("Itt tedd fel a kérdésedet, vagy adj meg témát amiről információt szeretnél megtudni:",
                                                      key="user_input_szabalyzat",)
    ##                                                  placeholder = st.session_state['kerdes_szabalyzat'])
                user_input_szabalyzat = user_input_szabalyzat.lower() #cachelés miatt 
                if st.form_submit_button('Keresés',
                                         on_click = kereses_button_szabalyzat):                              
##                    st.empty()
                    if user_input_szabalyzat:          
                        st.session_state['kerdes_szabalyzat'] = user_input_szabalyzat
                        print(f"Kérdés: {st.session_state['kerdes_szabalyzat']}")
                        print("Keresés típusa: Szabályzat")
                        # ------------- Tartalomjegyzék keresés ------------- 
                        # Fetch results from "DRV_tartalomjegyzek_szabalyzat"
                        find_and_store_toc_results_szabalyzat(user_input = st.session_state['kerdes_szabalyzat'], collection_name="DRV_tartalomjegyzek_szabalyzat")
                        
                ##        if not st.session_state['valaszok_toc']:
                ##            st.error("Nem található válasz a megadott kérésre.")

         
            # Display buttons for "DRV_tartalomjegyzek_szabalyzat" matches if results exist
            if st.session_state['search_complete_toc_szabalyzat'] and st.session_state['valaszok_toc_szabalyzat'] and st.session_state['kereses_popular_button_szabalyzat_pressed'] == False:
    ##            selected_tab = "Jogszabály"
    ##            selected_tab = "Szabályzat"
    ##            import pyautogui
    ##            if st.session_state['need_to_switch'] == True:
    ##                with st.empty():
    ####                    st.switch_page("user_manual.py")
    ####                    st.switch_page("main_page.py")
    ##                    pyautogui.hotkey("ctrl","F5")
    ##                    st.session_state['need_to_switch'] = False
    ##
          
                with st.spinner(f"Keresés: {st.session_state['kerdes_szabalyzat']}"):
              
                    with st.container():

    ##                        st.empty()

                            display_tartalomjegyzek_szabalyzat()

                            ## ------------- Cosine similiarity keresés ------------- 
                                
                            find_and_store_results_szabalyzat(user_input = st.session_state['kerdes_szabalyzat'], collection_name="DRV_szabalyzat")

                            ##------------- RAG -------------

                            if st.session_state['search_complete_szabalyzat'] == True:
                                rag_valasz_szabalyzat()

                            ##------------- Cosine similiarity találat mutatás -------------
                       
                            if st.session_state['search_complete_szabalyzat'] and st.session_state['valaszok_szabalyzat']:
                                display_valasz_szabalyzat()
                                show_more_szabalyzat()
                                st.session_state['kereses_button_szabalyzat_pressed'] = False
                                st.session_state['kereses_done_szabalyzat'] = True
                                st.session_state['reset'] = True
                            


        ##------------- Sidebar: Népszerű keresések -------------
##        @st.cache_data
        def top_popular_searches_szabalyzat(popular_search):
       
            st.session_state['kerdes_szabalyzat'] = popular_search.lower()
            print(f"Kérdés: {st.session_state['kerdes_szabalyzat']}")
            print("Keresés típusa: Szabályzat")
            find_and_store_toc_results_szabalyzat(user_input = st.session_state['kerdes_szabalyzat'], collection_name="DRV_tartalomjegyzek_szabalyzat")

            if st.session_state['search_complete_toc_szabalyzat'] and st.session_state['valaszok_toc_szabalyzat'] and st.session_state['kereses_popular_button_szabalyzat_pressed'] == True:
                with st.spinner(f"Keresés: {popular_search}"):
                    with st.container(): #ez kell, hogy elkülöníthessük a main kereséstől. st.rerun()-t callolva "lenullázzuk" az előző keresést, így nincsenek ütközések.

##                        st.empty()
##                        st.subheader(f"Kérdés: {popular_search}")
                        st.markdown(
                            f"<h3 style='text-align: center;'>Keresés: {popular_search}</h3>",
                            unsafe_allow_html=True
                        ) 
                        display_tartalomjegyzek_szabalyzat()
##                        st.empty()

                        ## ------------- Cosine similiarity keresés ------------- 
                            
                        find_and_store_results_szabalyzat(user_input = st.session_state['kerdes_szabalyzat'], collection_name="DRV_szabalyzat")

                        ##------------- RAG -------------

                        if st.session_state['search_complete_szabalyzat'] == True:
                            rag_valasz_szabalyzat()

                        ##------------- Cosine similiarity találat mutatás -------------
                   
                        if st.session_state['search_complete_szabalyzat'] and st.session_state['valaszok_szabalyzat']:
                            display_valasz_szabalyzat()
                            show_more_szabalyzat()
                            st.session_state['kereses_popular_button_szabalyzat_pressed'] = False
                            st.session_state['kereses_done_szabalyzat'] = True
                            st.session_state['reset'] = True


##                st.write(st.session_state['kerdes_szabalyzat'])

        def popular_search_button_szabalyzat():
##            st.empty()
            print("--------------------------------------------------------------------------")
        ##    print(f'Dátum: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}') #Ez valamiért kinyírja a programot. Mindegy, excel rögzít Összefoglalásnál dátumot is.
            print(f"Felhasználó: {st.session_state['username']}")
            selected_rag1 = None
            selected_rag2 = None
            st.session_state['kereses_popular_button_szabalyzat_pressed'] = True
            st.session_state['valasz_rag1_visszajelzes_szabalyzat'] = None                 
            st.session_state['kereses_button_szabalyzat'] += 1
            st.session_state['feedback_button1_pressed_szabalyzat'] = False
            st.session_state['feedback_button2_pressed_szabalyzat'] = False
            st.session_state['user_feedback_on_wrong_rag1_answer_given'] = False
            st.session_state['user_feedback_on_wrong_rag2_answer_given'] = False
            st.session_state['rag1_done_szabalyzat'] = False
            st.session_state['rag2_done_szabalyzat'] = False
            search_count_save(
                         username = st.session_state['username'],
                         kereses_button_pressed = st.session_state['kereses_button_szabalyzat'])
##            st.empty()




        def show_top_popular_buttons(popular_search):
            if st.button(popular_search,
                         help=f'Keresés indítása',
                         use_container_width=True,
                         on_click = popular_search_button_szabalyzat,
                         key = f"{popular_search}_button_szabalyzat"):
                with col2:
##                    st.empty()
##                    st.write(f"-----------------{popular_search}------------")
                    top_popular_searches_szabalyzat(popular_search)
##            st.button("népszerű téma2")
##            st.button("népszerű téma3")
##            st.button("népszerű téma4")
##            st.button("népszerű téma5")


        with col3:

            st.header("\n")
            st.markdown(
                "<h3 style='text-align: center;'>Népszerű keresések</h3>",
                unsafe_allow_html=True
            )            

            popular_searches = ["Használatbavételhez nyilatkozatot hol kérhetek?", "Ügyfélszolgálati elérhetőségek", "Mellékvízmérő csere költsége?", "Panaszt szeretnék tenni. Hol tehetem meg?", "Ivóvízbekötés díja?"]
            for popular_search in popular_searches:
                show_top_popular_buttons(popular_search)
            

##            popular_search = "Szakfelügyelet" # ide majd az excelből kinyert top keresés kell.
##
##            show_top_popular_buttons(popular_search)
##            st.write(st.session_state['kerdes_szabalyzat'])



    ##------------------------ Jogszabály ------------------------
                
    if selected_tab == "Jogszabály":
        content = st.container()
##            placeholder_jogszabaly = st.empty()
        
        with content:
##                content.empty()

            def kereses_button_jogszabaly():
##                    st.empty()
##                    content.empty()
                print("--------------------------------------------------------------------------")
            ##    print(f'Dátum: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}') #Ez valamiért kinyírja a programot. Mindegy, excel rögzít Összefoglalásnál dátumot is.
                print(f"Felhasználó: {st.session_state['username']}")
                st.session_state['kereses_button_jogszabaly'] += 1
                st.session_state['kereses_button_jogszabaly_pressed'] = True
                st.session_state['feedback_button1_pressed_jogszabaly'] = False
                st.session_state['feedback_button2_pressed_jogszabaly'] = False
                st.session_state['user_feedback_on_wrong_rag1_answer_given'] = False
                st.session_state['user_feedback_on_wrong_rag2_answer_given'] = False
                st.session_state['rag1_done_jogszabaly'] = False
                st.session_state['rag2_done_jogszabaly'] = False
                search_count_save(
                             username = st.session_state['username'],
                             kereses_button_pressed = st.session_state['kereses_button_jogszabaly'])
            
            if 'kereses_button_jogszabaly' not in st.session_state:
                initialize_session_states_jogszabaly()
            if 'kereses_popular_button_jogszabaly_pressed' not in st.session_state:
                initialize_session_states_szabalyzat()
            
            # Function to find matches and store them in session state
            def find_and_store_toc_results_jogszabaly(user_input, collection_name):
                organized_matches_toc, valaszok_toc, eleresi_helyek_toc, ids_toc, oldalszamok_toc, nevek_toc = find_matches(user_input, keresesek_szama, collection_name="Jogszabaly_tartalomjegyzek")
                # Store results in session state
                st.session_state['valaszok_toc_jogszabaly'] = valaszok_toc
                st.session_state['nevek_toc_jogszabaly'] = nevek_toc
                st.session_state['oldalszamok_toc_jogszabaly'] = oldalszamok_toc
                st.session_state['eleresi_helyek_toc_jogszabaly'] = eleresi_helyek_toc
                st.session_state['ids_toc_jogszabaly'] = ids_toc
                st.session_state['search_complete_toc_jogszabaly'] = True  # Mark search as complete
        ##            time.sleep(2)


            def display_tartalomjegyzek_jogszabaly():
                with st.container():
##                        st.empty()
                    st.subheader("Tartalomjegyzék találatok:", help=f"A találatra kattintva megnyitja az aktuális dokumentumot, de utána az oldalszámot nekünk kell beírni, hogy odaugorjon.")
                    for i in range(min(5, len(st.session_state['valaszok_toc_jogszabaly'][:5]))):
                ##        print(f"i értéke: {i}")
                ##        print(f"{st.session_state['nevek'][i]}")
                ##        print(f"{st.session_state['valaszok'][i]}")
                ##        print(f"{st.session_state['oldalszamok'][i]}")
                ##        print(f"{st.session_state['eleresi_helyek'][i]}")
                        st.link_button(
                            f"{st.session_state['nevek_toc_jogszabaly'][i]}: {st.session_state['valaszok_toc_jogszabaly'][i]}  . . . . . .  {st.session_state['oldalszamok_toc_jogszabaly'][i]}",
                            help=f'{st.session_state["nevek_toc_jogszabaly"][i]} megnyitása',
                            url = f"{st.session_state['eleresi_helyek_toc_jogszabaly'][i]}",
                            use_container_width=False,
                        )
##                        st.empty()
                    print(f"\nTartalomjegyzék találatok: \n{st.session_state['valaszok_toc_jogszabaly'][:5]}")


            # Function to find matches and store them in session state
            def find_and_store_results_jogszabaly(user_input, collection_name):
                organized_matches, valaszok, eleresi_helyek, ids, oldalszamok, nevek = find_matches(user_input, keresesek_szama, collection_name)
                # Store results in session state
                st.session_state['valaszok_jogszabaly'] = valaszok
                st.session_state['nevek_jogszabaly'] = nevek
                st.session_state['oldalszamok_jogszabaly'] = oldalszamok
                st.session_state['eleresi_helyek_jogszabaly'] = eleresi_helyek
                st.session_state['ids_jogszabaly'] = ids
                st.session_state['search_complete_jogszabaly'] = True  # Mark search as complete
        ##            time.sleep(5)


            def display_valasz_jogszabaly():
                st.divider()
                st.subheader("Pontos találatok a dokumentumokból a megadott válasz ellenőrzéséhez:", help="Független a Tartalomjegyzék találatoktól")
                for idx, (valasz, eleresi_hely, id_, nev, oldalszam) in enumerate(zip(
                        st.session_state['valaszok_jogszabaly'][:5],
                        st.session_state['eleresi_helyek_jogszabaly'][:5],
                        st.session_state['ids_jogszabaly'][:5],
                        st.session_state['nevek_jogszabaly'][:5],
                        st.session_state['oldalszamok_jogszabaly'][:5]), start=1):
                            
                    with st.container():
##                        st.subheader(f'{idx}. Találat: a(z) {nev} {oldalszam}. oldalán:') #később odafigyelni a névelőre, ha több doksi is hozzá lesz adva.
                        st.markdown(f"#### {idx}. Találat a [{nev}]({eleresi_hely}) {oldalszam}. oldalán:", unsafe_allow_html=True) #később odafigyelni a névelőre, ha több doksi is hozzá lesz adva.
                        st.text_area("label", value=valasz, height=400, key=f'valasz_jogszabaly{idx}', label_visibility="hidden")
                        id_number = int(id_[2:])
                        
                print("\nVálaszok mutatva")
    ##            print(f"\nVálasz 1. találat: \n{st.session_state['valaszok_jogszabaly'][0]}")

            @st.fragment()
            def show_more_jogszabaly():
                if st.button("Mutass többet", use_container_width=True):
                    for idx, (valasz, eleresi_hely, id_, nev, oldalszam) in enumerate(zip(
                            st.session_state['valaszok_jogszabaly'][5:10],
                            st.session_state['eleresi_helyek_jogszabaly'][5:10],
                            st.session_state['ids_jogszabaly'][5:10],
                            st.session_state['nevek_jogszabaly'][5:10],
                            st.session_state['oldalszamok_jogszabaly'][5:10]), start=6):
                        
                        with st.container():
                            st.markdown(f"#### {idx}. Találat a [{nev}]({eleresi_hely}) {oldalszam}. oldalán:", unsafe_allow_html=True)
                            st.text_area("label", value=valasz, height=400, key=f'valasz_jogszabaly{idx}', label_visibility="hidden")
                            id_number = int(id_[2:])
                 
                    print("\nTovábbi válaszok mutatva")


            def rag_valasz_jogszabaly():

                def rag1_button_disable_jogszabaly():
                    st.session_state['rag1_done_jogszabaly'] = True

                if 'rag1_done_jogszabaly' not in st.session_state:
                    st.session_state['rag1_done_jogszabaly'] = False

                if 'rag2_done_jogszabaly' not in st.session_state:
                    st.session_state['rag2_done_jogszabaly'] = False

    ##                if 'rag_search_running' not in st.session_state:
    ##                    st.session_state.rag_search_running = False
                if 'rag_search_running2' not in st.session_state:
                    st.session_state.rag_search_running2 = False

                if 'kerdes_jogszabaly_keyword_only' not in st.session_state:
                    st.session_state['kerdes_jogszabaly_keyword_only'] = ""

                def stream_data(rag_valasz):
                    st.empty()
                    rag_valasz = f"{rag_valasz}\n\n:blue[Ha pontosabb információt szeretnél megtudni a témáról, vagy további részletekre van szükséged, tedd fel **_konkrét kérdésedet!_**]\n\n *A megadott választ az alábbi gombokkal **értékelheted**.*"
                    for word in rag_valasz.split(" "):
                        yield word + " "
                        time.sleep(0.04)



                st.divider()    
    ##                if st.button('Kattints ide a találatok összefoglalásához, konkrét kérdés esetén annak megválaszolásához',
    ##                             help = "A demo erejéig korlátlan összefoglalás, később limitálva lesz",
    ##                             disabled=st.session_state.rag_search_running,
    ##                             key='rag1_button_jogszabaly',
    ##                             on_click = rag1_button_disable_jogszabaly):
    ##                    st.empty()
                response, token_usage, model = ask_question_with_rag(kerdes = st.session_state['kerdes_jogszabaly'], valaszok = st.session_state['valaszok_jogszabaly'], ids = st.session_state['ids_jogszabaly'], nev = st.session_state['nevek_jogszabaly'], oldalszam = st.session_state['oldalszamok_jogszabaly'])
                koltseg = costs(token_usage, model)
                st.session_state['valasz_rag1_jogszabaly'] = response
                st.session_state['koltseg_rag1_jogszabaly'] = koltseg
                st.session_state['model_rag1_jogszabaly'] = model
                st.session_state['valasz_rag2_jogszabaly'] = "-"
                st.session_state['koltseg_rag2_jogszabaly'] = "-"
                st.session_state['kerdes_jogszabaly_fragment'] = st.session_state['kerdes_jogszabaly']
        
                st.session_state['rag1_done_jogszabaly'] = True
                
                print("\nrag1_jogszabaly lefutott")
            ##        st.write(st.session_state)

                
                if st.session_state['rag1_done_jogszabaly'] == True and st.session_state['kerdes_jogszabaly_fragment'] == st.session_state['kerdes_jogszabaly']: #ez utóbbi azért kell, hogy ha megváltozik a kérdés ne mutassa az előző összefoglalást
                    with st.container():
##                            content.empty()
                        if st.session_state['kereses_popular_button_jogszabaly_pressed'] == True:
                            ## Using simple markdown/write:
                            st.markdown(f"{st.session_state['valasz_rag1_jogszabaly']}\n\n :blue[Ha pontosabb információt szeretnél megtudni a témáról, vagy további részletekre van szükséged, tedd fel **_konkrét kérdésedet!_**]\n\n *A megadott választ az alábbi gombokkal **értékelheted**.*")
                            st.session_state['kereses_done_jogszabaly'] = False
                            
##                    st.empty()
                    with st.container():
##                            content.empty()
                        if st.session_state['kereses_popular_button_jogszabaly_pressed'] == False and st.session_state['kereses_done_jogszabaly'] == False: #ez így sosem executeol, adatbázis kell majd, ellenőrizni, hogy miket cacheltünk korábban.
                            ## Using streaming(later):
                            st.markdown(f"{st.session_state['valasz_rag1_jogszabaly']}\n\n :blue[Ha pontosabb információt szeretnél megtudni a témáról, vagy további részletekre van szükséged, tedd fel **_konkrét kérdésedet!_**]\n\n *A megadott választ az alábbi gombokkal **értékelheted**.*")
##                            st.write_stream(stream_data(st.session_state['valasz_rag1_jogszabaly']))
                        if st.session_state['kereses_popular_button_jogszabaly_pressed'] == False and st.session_state['kereses_done_jogszabaly'] == True:
                            st.caption(f"{st.session_state['kerdes_jogszabaly']}")                            
                            st.markdown(f"{st.session_state['valasz_rag1_jogszabaly']}\n\n :blue[Ha pontosabb információt szeretnél megtudni a témáról, vagy további részletekre van szükséged, tedd fel **_konkrét kérdésedet!_**]\n\n *A megadott választ az alábbi gombokkal **értékelheted**.*")
        ##                st.markdown(f"Költség: {st.session_state['koltseg_rag1_jogszabaly']} Ft")
                            st.session_state['kereses_done_jogszabaly'] = False
                        store_data_in_excel_jogszabaly(st.session_state['kerdes_jogszabaly'], st.session_state['valasz_rag1_jogszabaly'], st.session_state['valasz_rag2_jogszabaly'],
                                                     st.session_state['koltseg_rag1_jogszabaly'], st.session_state['koltseg_rag2_jogszabaly'], st.session_state['model_rag1_jogszabaly'], st.session_state['username'])
                        rag_feedback(key="feedback_rag1_jogszabaly")
                        st.caption(":red[Fontos:] az összefoglalt válasz lehet pontatlan, akár téves is. A megadott választ minden esetben ellenőrizni kell!")


                if st.session_state['rag1_done_jogszabaly'] == True:

                    @st.fragment()
                    def rag2_jogszabaly_start():

                        def rag2_button_disable_jogszabaly():
                            st.empty() # ez kell!
                            st.session_state['rag2_done_jogszabaly'] = True
                            st.session_state.rag_search_running2 = True
                  
                        if st.button("Újrapróbálkozás a kérdés automatikus átfogalmazásával",
                                     help=f'Bonyolultabb kérdés esetén más módszerrel próbál választ adni. \n\nEgyszerű témánál nem változik a válasz.',
                                     disabled=st.session_state.rag_search_running2,
                                     on_click = rag2_button_disable_jogszabaly,
                                     key = "rag2_button_jogszabaly"):
                            st.empty()
                            st.session_state['kerdes_jogszabaly_keyword_only'] = refactor_question_keyword_only(kerdes = st.session_state['kerdes_jogszabaly']) #Nem jó, a válaszokat kell refactorálni, hogy a rag azokban keresse a választ!!! Most nem fontos, majd fixálni kell. Ez most csak annyit csinál, hogy a fő témára rákeres és megpróbál minden hasznos infot elmondani róla.
                            response, token_usage, model = ask_question_with_rag(kerdes = st.session_state['kerdes_jogszabaly_keyword_only'], valaszok = st.session_state['valaszok_jogszabaly'], ids = st.session_state['ids_jogszabaly'], nev = st.session_state['nevek_jogszabaly'], oldalszam = st.session_state['oldalszamok_jogszabaly'])
                            koltseg = costs(token_usage, model)
                            st.session_state['valasz_rag2_jogszabaly'] = response
                            st.session_state['koltseg_rag2_jogszabaly'] = koltseg
                            st.session_state['model_rag1_jogszabaly'] = model
                            st.session_state['rag2_done_jogszabaly'] = True
                            print("\nrag2_jogszabaly lefutott")

                        if st.session_state['rag2_done_jogszabaly'] == True and st.session_state['kerdes_jogszabaly_fragment'] == st.session_state['kerdes_jogszabaly']: #ez utóbbi azért kell, hogy ha megváltozik a kérdés ne mutassa az előző összefoglalást
                            st.header(f'Alternatív válasz:')
                            st.text_area("rag2_label_jogszabaly",
                                         value=f"{st.session_state['valasz_rag2_jogszabaly']}\n\n:blue[Ha pontosabb információt szeretnél megtudni a témáról, vagy további részletekre van szükséged, tedd fel **_konkrét kérdésedet!_**]\n\n *A megadott választ az alábbi gombokkal **értékelheted**.*",
                                         height=400,
                                         key="valasz_rag2_jogszabaly_text_area",
                                         label_visibility="hidden")
                ##            st.markdown(f"Költség: {st.session_state['koltseg_rag1_jogszabaly']} Ft")
                            store_data_in_excel_jogszabaly(st.session_state['kerdes_jogszabaly'], st.session_state['valasz_rag1_jogszabaly'], st.session_state['valasz_rag2_jogszabaly'],
                                                         st.session_state['koltseg_rag1_jogszabaly'], st.session_state['koltseg_rag2_jogszabaly'], st.session_state['model_rag1_jogszabaly'], st.session_state['username'])
                            rag_feedback(key="feedback_rag2_jogszabaly")
                            st.caption(":red[Fontos:] az összefoglalt válasz lehet pontatlan, akár téves is. A megadott választ minden esetben ellenőrizni kell!")
                            

                        if st.session_state['rag1_done_jogszabaly'] == True and st.session_state['rag2_done_jogszabaly'] == True:
                            st.session_state.rag_search_running2 = False  # Re-enable Button 2 after processing
                            st.session_state.rag_search_running = False   # Re-enable Button 1 after processing
                            st.session_state['rag2_done_jogszabaly'] = False
                            st.error("Nincs több összefoglalt válasz.")

##                    rag2_jogszabaly_start()


            

            with st.form("my_form", border = False):    
                # Text box for user input
                user_input_jogszabaly = st.text_input("Itt tedd fel a kérdésedet, vagy adj meg témát amiről információt szeretnél megtudni:",
                                                      key="user_input_jogszabaly",)
    ##                                                  placeholder = st.session_state['kerdes_jogszabaly'])
                user_input_jogszabaly = user_input_jogszabaly.lower() #cachelés miatt 
                if st.form_submit_button('Keresés',
                                         on_click = kereses_button_jogszabaly):                              
##                        st.empty()
                    if user_input_jogszabaly:          
                        st.session_state['kerdes_jogszabaly'] = user_input_jogszabaly
                        print(f"Kérdés: {st.session_state['kerdes_jogszabaly']}")
                        print("Keresés típusa: jogszabály")
                        # ------------- Tartalomjegyzék keresés ------------- 
                        # Fetch results from "Jogszabaly_tartalomjegyzek"
                        find_and_store_toc_results_jogszabaly(user_input = st.session_state['kerdes_jogszabaly'], collection_name="Jogszabaly_tartalomjegyzek")
                        
                ##        if not st.session_state['valaszok_toc']:
                ##            st.error("Nem található válasz a megadott kérésre.")

         
            # Display buttons for "Jogszabaly_tartalomjegyzek" matches if results exist
            if st.session_state['search_complete_toc_jogszabaly'] and st.session_state['valaszok_toc_jogszabaly'] and st.session_state['kereses_popular_button_jogszabaly_pressed'] == False:
    ##            selected_tab = "Jogszabály"
    ##            selected_tab = "jogszabály"
    ##            import pyautogui
    ##            if st.session_state['need_to_switch'] == True:
    ##                with st.empty():
    ####                    st.switch_page("user_manual.py")
    ####                    st.switch_page("main_page.py")
    ##                    pyautogui.hotkey("ctrl","F5")
    ##                    st.session_state['need_to_switch'] = False
    ##                
                with st.spinner(f"Keresés: {st.session_state['kerdes_jogszabaly']}"):
      

                    with st.container():
##                            st.empty()

                        display_tartalomjegyzek_jogszabaly()

                        ## ------------- Cosine similiarity keresés ------------- 
                            
                        find_and_store_results_jogszabaly(user_input = st.session_state['kerdes_jogszabaly'], collection_name="Jogszabaly")

                        ##------------- RAG -------------

                        if st.session_state['search_complete_jogszabaly'] == True:
                            rag_valasz_jogszabaly()

                        ##------------- Cosine similiarity találat mutatás -------------
                   
                        if st.session_state['search_complete_jogszabaly'] and st.session_state['valaszok_jogszabaly']:
                            display_valasz_jogszabaly()
                            show_more_jogszabaly()
                            st.session_state['reset'] = True
                            st.session_state['kereses_button_jogszabaly'] = False
                            st.session_state['kereses_done_jogszabaly'] = True

        ##------------- Sidebar: Népszerű keresések -------------
##        @st.cache_data
        def top_popular_searches_jogszabaly(popular_search):
       
            st.session_state['kerdes_jogszabaly'] = popular_search.lower()
            print(f"Kérdés: {st.session_state['kerdes_jogszabaly']}")
            print("Keresés típusa: jogszabály")
            find_and_store_toc_results_jogszabaly(user_input = st.session_state['kerdes_jogszabaly'], collection_name="Jogszabaly_tartalomjegyzek")

            if st.session_state['search_complete_toc_jogszabaly'] and st.session_state['valaszok_toc_jogszabaly'] and st.session_state['kereses_popular_button_jogszabaly_pressed'] == True:
                with st.spinner(f"Keresés: {popular_search}"):
                    with st.container(): #ez kell, hogy elkülöníthessük a main kereséstől. st.rerun()-t callolva "lenullázzuk" az előző keresést, így nincsenek ütközések.

##                            st.empty()
##                        st.subheader(f"Kérdés: {popular_search}")
                        st.markdown(
                            f"<h3 style='text-align: center;'>Keresés: {popular_search}</h3>",
                            unsafe_allow_html=True
                        ) 
                        display_tartalomjegyzek_jogszabaly()
##                        st.empty()

                        ## ------------- Cosine similiarity keresés ------------- 
                            
                        find_and_store_results_jogszabaly(user_input = st.session_state['kerdes_jogszabaly'], collection_name="Jogszabaly")

                        ##------------- RAG -------------

                        if st.session_state['search_complete_jogszabaly'] == True:
                            rag_valasz_jogszabaly()

                        ##------------- Cosine similiarity találat mutatás -------------
                   
                        if st.session_state['search_complete_jogszabaly'] and st.session_state['valaszok_jogszabaly']:
                            display_valasz_jogszabaly()
                            show_more_jogszabaly()
                            st.session_state['reset'] = True
                            st.session_state['kereses_popular_button_jogszabaly_pressed'] = False
                            st.session_state['kereses_done_jogszabaly'] = True


##                st.write(st.session_state['kerdes_jogszabaly'])

        def popular_search_button_jogszabaly():
##                st.empty()
            print("--------------------------------------------------------------------------")
        ##    print(f'Dátum: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}') #Ez valamiért kinyírja a programot. Mindegy, excel rögzít Összefoglalásnál dátumot is.
            print(f"Felhasználó: {st.session_state['username']}")
            selected_rag1 = None
            selected_rag2 = None
            st.session_state['kereses_popular_button_jogszabaly_pressed'] = True
            st.session_state['valasz_rag1_visszajelzes_jogszabaly'] = None                 
            st.session_state['kereses_button_jogszabaly'] += 1
            st.session_state['feedback_button1_pressed_jogszabaly'] = False
            st.session_state['feedback_button2_pressed_jogszabaly'] = False
            st.session_state['user_feedback_on_wrong_rag1_answer_given'] = False
            st.session_state['user_feedback_on_wrong_rag2_answer_given'] = False
            st.session_state['rag1_done_jogszabaly'] = False
            st.session_state['rag2_done_jogszabaly'] = False
            search_count_save(
                         username = st.session_state['username'],
                         kereses_button_pressed = st.session_state['kereses_button_jogszabaly'])
##                st.empty()




        def show_top_popular_buttons(popular_search):
            if st.button(popular_search,
                         help=f'Keresés indítása',
                         use_container_width=True,
                         on_click = popular_search_button_jogszabaly,
                         key = f"{popular_search}_button_jogszabaly"):
                with col2:
##                        st.empty()
##                    st.write(f"-----------------{popular_search}------------")
                    top_popular_searches_jogszabaly(popular_search)
##            st.button("népszerű téma2")
##            st.button("népszerű téma3")
##            st.button("népszerű téma4")
##            st.button("népszerű téma5")


        with col3:

            st.header("\n")
            st.markdown(
                "<h3 style='text-align: center;'>Népszerű keresések</h3>",
                unsafe_allow_html=True
            )            

            popular_searches = ["Lehet egynél több vízbekötése egy ingatlannak?", "Közműfejlesztés", "szolgáltatási pontok", "Bekötési tervdokumentációnak mit kell tartalmaznia?", "közös szennyvízbekötés feltételei"]
            for popular_search in popular_searches:
                show_top_popular_buttons(popular_search)
            

##            popular_search = "Szakfelügyelet" # ide majd az excelből kinyert top keresés kell.
##
##            show_top_popular_buttons(popular_search)
##            st.write(st.session_state['kerdes_jogszabaly'])






    ##------------------------ Tájékoztató ------------------------

    if selected_tab == "Tájékoztató":
        content = st.container()
        placeholder_tajekoztato = st.empty()
        
        with content:
            content.empty()

            def kereses_button_tajekoztato():
                st.empty()
                content.empty()
                print("--------------------------------------------------------------------------")
            ##    print(f'Dátum: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}') #Ez valamiért kinyírja a programot. Mindegy, excel rögzít Összefoglalásnál dátumot is.
                print(f"Felhasználó: {st.session_state['username']}")
                st.session_state['kereses_button_tajekoztato_pressed'] = True
                st.session_state['kereses_button_tajekoztato'] += 1
                st.session_state['feedback_button1_pressed_tajekoztato'] = False
                st.session_state['feedback_button2_pressed_tajekoztato'] = False
                st.session_state['user_feedback_on_wrong_rag1_answer_given'] = False
                st.session_state['user_feedback_on_wrong_rag2_answer_given'] = False
                st.session_state['rag1_done_tajekoztato'] = False
                st.session_state['rag2_done_tajekoztato'] = False
                search_count_save(
                             username = st.session_state['username'],
                             kereses_button_pressed = st.session_state['kereses_button_tajekoztato'])
            
            if 'kereses_button_tajekoztato' not in st.session_state:
                initialize_session_states_tajekoztato()
            if 'kereses_popular_button_tajekoztato_pressed' not in st.session_state:
                initialize_session_states_szabalyzat()            

            # Function to find matches and store them in session state
            def find_and_store_results_tajekoztato(user_input, collection_name):
                organized_matches, valaszok, eleresi_helyek, ids, oldalszamok, nevek = find_matches(user_input, keresesek_szama, collection_name)
                # Store results in session state
                st.session_state['valaszok_tajekoztato'] = valaszok
                st.session_state['nevek_tajekoztato'] = nevek
                st.session_state['oldalszamok_tajekoztato'] = oldalszamok
                st.session_state['eleresi_helyek_tajekoztato'] = eleresi_helyek
                st.session_state['ids_tajekoztato'] = ids
                st.session_state['search_complete_tajekoztato'] = True  # Mark search as complete
        ##            time.sleep(5)


            def display_valasz_tajekoztato():
                st.divider()
                st.subheader("Pontos találatok a dokumentumokból a megadott válasz ellenőrzéséhez:", help="Független a Tartalomjegyzék találatoktól")
                for idx, (valasz, eleresi_hely, id_) in enumerate(zip(
                        st.session_state['valaszok_tajekoztato'][:5],
                        st.session_state['eleresi_helyek_tajekoztato'][:5],
                        st.session_state['ids_tajekoztato'][:5]), start=1):
                    
                    with st.container():
                        st.subheader(f'{idx}. Találat:')
                        st.text_area("label", value=valasz, height=400, key=f'valasz_tajekoztato{idx}', label_visibility="hidden")
                        st.markdown(f"Elérési hely: {eleresi_hely}", unsafe_allow_html=True)
                        id_number = int(id_[2:])
                       
                        
                        # Page number finding process
                        page_number = find_page_number_tajekoztato(text=valasz) #átdolgozandó, eleve legyen hozzárendelve a chunkhoz az oldalszám, ne itt keresgéljük
                        while True:
                            
                            if page_number != None:
                                st.markdown(f"{page_number}. oldal")
                                break

                            else:
                                
                                valaszok = find_last_page_number_tajekoztato(id_number)
                                for valasz in zip(valaszok):
                                    page_number = find_page_number_tajekoztato(text=valasz[0][0])
                                    id_number = id_number - 1
                                    continue
                print("\nVálaszok mutatva")
    ##            print(f"\nVálasz 1. találat: \n{st.session_state['valaszok_tajekoztato'][0]}")

            @st.fragment()
            def show_more_tajekoztato():
                if st.button("Mutass többet", use_container_width=True):
                    for idx, (valasz, eleresi_hely, id_) in enumerate(zip(
                            st.session_state['valaszok_tajekoztato'][5:10],
                            st.session_state['eleresi_helyek_tajekoztato'][5:10],
                            st.session_state['ids_tajekoztato'][5:10]), start=6):
                        
                        with st.container():
                            st.subheader(f'{idx}. Találat:')
                            st.text_area("label", value=valasz, height=400, key=f'valasz_tajekoztato{idx}', label_visibility="hidden")
                            st.markdown(f"Elérési hely: {eleresi_hely}", unsafe_allow_html=True)
                            id_number = int(id_[2:])
                            
                            # Page number finding process
                            page_number = find_page_number_tajekoztato(text=valasz)
                            while True:
                                
                                if page_number != None:
                                    st.markdown(f"{page_number}. oldal")
                                    break

                                else:
                                    
                                    valaszok = find_last_page_number_tajekoztato(id_number)
                                    for valasz in zip(valaszok):
                                        page_number = find_page_number_tajekoztato(text=valasz[0][0])
                                        id_number = id_number - 1
                                        continue                    
                    print("\nTovábbi válaszok mutatva")


            def rag_valasz_tajekoztato():

                def rag1_button_disable_tajekoztato():
                    st.session_state['rag1_done_tajekoztato'] = True

                if 'rag1_done_tajekoztato' not in st.session_state:
                    st.session_state['rag1_done_tajekoztato'] = False

                if 'rag2_done_tajekoztato' not in st.session_state:
                    st.session_state['rag2_done_tajekoztato'] = False

    ##                if 'rag_search_running' not in st.session_state:
    ##                    st.session_state.rag_search_running = False
                if 'rag_search_running2' not in st.session_state:
                    st.session_state.rag_search_running2 = False

                if 'kerdes_tajekoztato_keyword_only' not in st.session_state:
                    st.session_state['kerdes_tajekoztato_keyword_only'] = ""

                def stream_data(rag_valasz):
                    st.empty()
                    rag_valasz = f"{rag_valasz}\n\n:blue[Ha pontosabb információt szeretnél megtudni a témáról, vagy további részletekre van szükséged, tedd fel **_konkrét kérdésedet!_**]\n\n *A megadott választ az alábbi gombokkal **értékelheted**.*"
                    for word in rag_valasz.split(" "):
                        yield word + " "
                        time.sleep(0.04)



                st.divider()    
    ##                if st.button('Kattints ide a találatok összefoglalásához, konkrét kérdés esetén annak megválaszolásához',
    ##                             help = "A demo erejéig korlátlan összefoglalás, később limitálva lesz",
    ##                             disabled=st.session_state.rag_search_running,
    ##                             key='rag1_button_tajekoztato',
    ##                             on_click = rag1_button_disable_tajekoztato):
    ##                    st.empty()
                response, token_usage, model = ask_question_with_rag(kerdes = st.session_state['kerdes_tajekoztato'], valaszok = st.session_state['valaszok_tajekoztato'], ids = st.session_state['ids_tajekoztato'], nev = st.session_state['nevek_tajekoztato'], oldalszam = st.session_state['oldalszamok_tajekoztato'])
                koltseg = costs(token_usage, model)
                st.session_state['valasz_rag1_tajekoztato'] = response
                st.session_state['koltseg_rag1_tajekoztato'] = koltseg
                st.session_state['model_rag1_tajekoztato'] = model
                st.session_state['valasz_rag2_tajekoztato'] = "-"
                st.session_state['koltseg_rag2_tajekoztato'] = "-"
                st.session_state['kerdes_tajekoztato_fragment'] = st.session_state['kerdes_tajekoztato']
        
                st.session_state['rag1_done_tajekoztato'] = True
                
                print("\nrag1_tajekoztato lefutott")
            ##        st.write(st.session_state)

                if st.session_state['rag1_done_tajekoztato'] == True and st.session_state['kerdes_tajekoztato_fragment'] == st.session_state['kerdes_tajekoztato']: #ez utóbbi azért kell, hogy ha megváltozik a kérdés ne mutassa az előző összefoglalást
                    with st.container():
                        content.empty()
                        if st.session_state['kereses_popular_button_tajekoztato_pressed'] == True:
                            ## Using simple markdown/write:
                            st.markdown(f"{st.session_state['valasz_rag1_tajekoztato']}\n\n :blue[Ha pontosabb információt szeretnél megtudni a témáról, vagy további részletekre van szükséged, tedd fel **_konkrét kérdésedet!_**]\n\n *A megadott választ az alábbi gombokkal **értékelheted**.*")
                            st.session_state['kereses_done_tajekoztato'] = False
##                    st.empty()
                    with st.container():
                        content.empty()
                        if st.session_state['kereses_popular_button_tajekoztato_pressed'] == False and st.session_state['kereses_done_tajekoztato'] == False:
                            ## Using streaming(later):
                            st.markdown(f"{st.session_state['valasz_rag1_tajekoztato']}\n\n :blue[Ha pontosabb információt szeretnél megtudni a témáról, vagy további részletekre van szükséged, tedd fel **_konkrét kérdésedet!_**]\n\n *A megadott választ az alábbi gombokkal **értékelheted**.*")                           
##                            st.write_stream(stream_data(st.session_state['valasz_rag1_tajekoztato']))
                        if st.session_state['kereses_popular_button_tajekoztato_pressed'] == False and st.session_state['kereses_done_tajekoztato'] == True:
                            st.caption(f"Indított keresés: {st.session_state['kerdes_tajekoztato']}")
                            st.markdown(f"{st.session_state['valasz_rag1_tajekoztato']}\n\n :blue[Ha pontosabb információt szeretnél megtudni a témáról, vagy további részletekre van szükséged, tedd fel **_konkrét kérdésedet!_**]\n\n *A megadott választ az alábbi gombokkal **értékelheted**.*")
##                            st.markdown(f"Költség: {st.session_state['koltseg_rag1_tajekoztato']} Ft")
                            st.session_state['kereses_done_tajekoztato'] = False


                        store_data_in_excel_tajekoztato(st.session_state['kerdes_tajekoztato'], st.session_state['valasz_rag1_tajekoztato'], st.session_state['valasz_rag2_tajekoztato'],
                                                     st.session_state['koltseg_rag1_tajekoztato'], st.session_state['koltseg_rag2_tajekoztato'], st.session_state['model_rag1_tajekoztato'], st.session_state['username'])
                        rag_feedback(key="feedback_rag1_tajekoztato")
                        st.caption(":red[Fontos:] az összefoglalt válasz lehet pontatlan, akár téves is. A megadott választ minden esetben ellenőrizni kell!")


                if st.session_state['rag1_done_tajekoztato'] == True:

                    @st.fragment()
                    def rag2_tajekoztato_start():

                        def rag2_button_disable_tajekoztato():
                            st.empty() # ez kell!
                            st.session_state['rag2_done_tajekoztato'] = True
                            st.session_state.rag_search_running2 = True
                  
                        if st.button("Újrapróbálkozás a kérdés automatikus átfogalmazásával",
                                     help=f'Bonyolultabb kérdés esetén más módszerrel próbál választ adni. \n\nEgyszerű témánál nem változik a válasz.',
                                     disabled=st.session_state.rag_search_running2,
                                     on_click = rag2_button_disable_tajekoztato,
                                     key = "rag2_button_tajekoztato"):
                            st.empty()
                            st.session_state['kerdes_tajekoztato_keyword_only'] = refactor_question_keyword_only(kerdes = st.session_state['kerdes_tajekoztato']) #Nem jó, a válaszokat kell refactorálni, hogy a rag azokban keresse a választ!!! Most nem fontos, majd fixálni kell. Ez most csak annyit csinál, hogy a fő témára rákeres és megpróbál minden hasznos infot elmondani róla.
                            response, token_usage, model = ask_question_with_rag(kerdes = st.session_state['kerdes_tajekoztato_keyword_only'], valaszok = st.session_state['valaszok_tajekoztato'], ids = st.session_state['ids_tajekoztato'], nev = st.session_state['nevek_tajekoztato'], oldalszam = st.session_state['oldalszamok_tajekoztato'])
                            koltseg = costs(token_usage, model)
                            st.session_state['valasz_rag2_tajekoztato'] = response
                            st.session_state['koltseg_rag2_tajekoztato'] = koltseg
                            st.session_state['model_rag1_tajekoztato'] = model
                            st.session_state['rag2_done_tajekoztato'] = True
                            print("\nrag2_tajekoztato lefutott")

                        if st.session_state['rag2_done_tajekoztato'] == True and st.session_state['kerdes_tajekoztato_fragment'] == st.session_state['kerdes_tajekoztato']: #ez utóbbi azért kell, hogy ha megváltozik a kérdés ne mutassa az előző összefoglalást
                            st.header(f'Alternatív válasz:')
                            st.text_area("rag2_label_tajekoztato",
                                         value=f"{st.session_state['valasz_rag2_tajekoztato']}\n\n:blue[Ha pontosabb információt szeretnél megtudni a témáról, vagy további részletekre van szükséged, tedd fel **_konkrét kérdésedet!_**]\n\n *A megadott választ az alábbi gombokkal **értékelheted**.*",
                                         height=400,
                                         key="valasz_rag2_tajekoztato_text_area",
                                         label_visibility="hidden")
                ##            st.markdown(f"Költség: {st.session_state['koltseg_rag1_tajekoztato']} Ft")
                            store_data_in_excel_tajekoztato(st.session_state['kerdes_tajekoztato'], st.session_state['valasz_rag1_tajekoztato'], st.session_state['valasz_rag2_tajekoztato'],
                                                         st.session_state['koltseg_rag1_tajekoztato'], st.session_state['koltseg_rag2_tajekoztato'], st.session_state['model_rag1_tajekoztato'], st.session_state['username'])
                            rag_feedback(key="feedback_rag2_tajekoztato")
                            st.caption(":red[Fontos:] az összefoglalt válasz lehet pontatlan, akár téves is. A megadott választ minden esetben ellenőrizni kell!")
                            

                        if st.session_state['rag1_done_tajekoztato'] == True and st.session_state['rag2_done_tajekoztato'] == True:
                            st.session_state.rag_search_running2 = False  # Re-enable Button 2 after processing
                            st.session_state.rag_search_running = False   # Re-enable Button 1 after processing
                            st.session_state['rag2_done_tajekoztato'] = False
                            st.error("Nincs több összefoglalt válasz.")

                    rag2_tajekoztato_start()


            

            with st.form("my_form", border = False):    
                # Text box for user input
                user_input_tajekoztato = st.text_input("Itt tedd fel a kérdésedet, vagy adj meg témát amiről információt szeretnél megtudni:",
                                                      key="user_input_tajekoztato",)
    ##                                                  placeholder = st.session_state['kerdes_tajekoztato'])
                user_input_tajekoztato = user_input_tajekoztato.lower() #cachelés miatt 
                if st.form_submit_button('Keresés',
                                         on_click = kereses_button_tajekoztato):                              
                    st.empty()
                    if user_input_tajekoztato:          
                        st.session_state['kerdes_tajekoztato'] = user_input_tajekoztato
                        print(f"Kérdés: {st.session_state['kerdes_tajekoztato']}")
                        print("Keresés típusa: tájákoztató")


            if st.session_state['kereses_popular_button_tajekoztato_pressed'] == False and st.session_state['kereses_button_tajekoztato'] == True:
                
                with st.spinner(f"Keresés: {st.session_state['kerdes_tajekoztato']}"):
      
                    with st.container():
                        st.empty()

                        ## ------------- Cosine similiarity keresés ------------- 
                            
                        find_and_store_results_tajekoztato(user_input = st.session_state['kerdes_tajekoztato'], collection_name="DRV_tajekoztato")

                        ##------------- RAG -------------

                        if st.session_state['search_complete_tajekoztato'] == True:
                            rag_valasz_tajekoztato()

                        ##------------- Cosine similiarity találat mutatás -------------
                   
                        if st.session_state['search_complete_tajekoztato'] and st.session_state['valaszok_tajekoztato']:  
                            display_valasz_tajekoztato()
                            show_more_tajekoztato()
                            st.session_state['reset'] = True
                            st.session_state['kereses_button_tajekoztato'] = False
                            st.session_state['kereses_done_tajekoztato'] = True                         

        ##------------- Sidebar: Népszerű keresések -------------
##        @st.cache_data
        def top_popular_searches_tajekoztato(popular_search):
       
            st.session_state['kerdes_tajekoztato'] = popular_search.lower()
            print(f"Kérdés: {st.session_state['kerdes_tajekoztato']}")
            print("Keresés típusa: tájákoztató")


            if st.session_state['kereses_popular_button_tajekoztato_pressed'] == True:
                with st.spinner(f"Keresés: {popular_search}"):
                    with st.container(): #ez kell, hogy elkülöníthessük a main kereséstől.

                        st.empty()
##                        st.subheader(f"Kérdés: {popular_search}")
                        st.markdown(
                            f"<h3 style='text-align: center;'>Keresés: {popular_search}</h3>",
                            unsafe_allow_html=True
                        ) 

##                        st.empty()

                        ## ------------- Cosine similiarity keresés ------------- 
                            
                        find_and_store_results_tajekoztato(user_input = st.session_state['kerdes_tajekoztato'], collection_name="DRV_tajekoztato")

                        ##------------- RAG -------------

                        if st.session_state['search_complete_tajekoztato'] == True:
                            rag_valasz_tajekoztato()

                        ##------------- Cosine similiarity találat mutatás -------------
                   
                        if st.session_state['search_complete_tajekoztato'] and st.session_state['valaszok_tajekoztato']:
                            display_valasz_tajekoztato()
                            show_more_tajekoztato()
                            st.session_state['reset'] = True
                            st.session_state['kereses_popular_button_tajekoztato_pressed'] = False
                            st.session_state['kereses_done_tajekoztato'] = True

##                st.write(st.session_state['kerdes_tajekoztato'])

        def popular_search_button_tajekoztato():
            st.empty()
            print("--------------------------------------------------------------------------")
        ##    print(f'Dátum: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}') #Ez valamiért kinyírja a programot. Mindegy, excel rögzít Összefoglalásnál dátumot is.
            print(f"Felhasználó: {st.session_state['username']}")
            selected_rag1 = None
            selected_rag2 = None
            st.session_state['kereses_popular_button_tajekoztato_pressed'] = True
            st.session_state['valasz_rag1_visszajelzes_tajekoztato'] = None                 
            st.session_state['kereses_button_tajekoztato'] += 1
            st.session_state['feedback_button1_pressed_tajekoztato'] = False
            st.session_state['feedback_button2_pressed_tajekoztato'] = False
            st.session_state['user_feedback_on_wrong_rag1_answer_given'] = False
            st.session_state['user_feedback_on_wrong_rag2_answer_given'] = False
            st.session_state['rag1_done_tajekoztato'] = False
            st.session_state['rag2_done_tajekoztato'] = False
            search_count_save(
                         username = st.session_state['username'],
                         kereses_button_pressed = st.session_state['kereses_button_tajekoztato'])
            st.empty()




        def show_top_popular_buttons(popular_search):
            if st.button(popular_search,
                         help=f'Keresés indítása',
                         use_container_width=True,
                         on_click = popular_search_button_tajekoztato,
                         key = f"{popular_search}_button_tajekoztato"):
                with col2:
                    st.empty()
##                    st.write(f"-----------------{popular_search}------------")
                    top_popular_searches_tajekoztato(popular_search)
##            st.button("népszerű téma2")
##            st.button("népszerű téma3")
##            st.button("népszerű téma4")
##            st.button("népszerű téma5")


        with col3:

            st.header("\n")
            st.markdown(
                "<h3 style='text-align: center;'>Népszerű keresések</h3>",
                unsafe_allow_html=True
            )            

            popular_searches = ["Vízbekötés", "Ikresítés", "Szakfelügyelet", "Külsős kivitelező építheti a vízbekötést?", "Bekötésnél mi a felhasználó felelőssége?"]
            for popular_search in popular_searches:
                show_top_popular_buttons(popular_search)
            

##            popular_search = "Szakfelügyelet" # ide majd az excelből kinyert top keresés kell.
##
##            show_top_popular_buttons(popular_search)
##            st.write(st.session_state['kerdes_tajekoztato'])



