import streamlit as st

col1, col2, col3 = st.columns([1,3,1])

with col2:
    st.markdown(
        "<h1 style='text-align: center;'>Használati útmutató</h1>",
        unsafe_allow_html=True
    )


    st.header("Keresés")
    st.markdown("""<div style='text-align: justify;'>A Kereső minden alkalommal felkínálja a vonatkozó tartalomjegyzék találatokat, majd a program összefoglalja a témára vonatkozó információkat, vagy megválaszolja a feltett kérdést.
Ezt követően felkínál 5 db, a keresett információt tartalmazó pontos részletet a dokumentumokból.
                    <br>
                    A tartalomjegyzék találat tartalmazza a dokumentum nevét, a talált témát és annak az oldalszámát. Erre kattintva új lapon megnyílik a dokumentum, amiben az oldalszámot beírva a keresett témára ugorhatunk.
                    <br>
                    Jelenleg a keresés az alábbi módszerekkel lehetséges. A program a kérdés alapján automatikusan eldönti melyik módszert alkalmazza.
                </div>""", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Kulcsszavas keresés", "Konkrét kérdés", "Jelentés alapú keresés"])


    with tab1:
        st.markdown(
            "<div style='text-align: center;'>Példa keresés: vízbekötés</div>",
            unsafe_allow_html=True
        )
        
        left1, right1 = st.columns(2)

        with left1:
            st.image(r"user_manual\vizbekotes_tartalomjegyzek.png")
            st.image(r"user_manual\vizbekotes_kereses.png")
        with right1:       
            st.markdown(
                """
                <div style='text-align: justify;'>
                    <br><br>
                    Kulcsszavas keresésnél a program az általános információkat fogja megadni, majd felkínálja, hogy a keresés pontosításával konkrét válaszokat is tud adni.
                    <br><br>
                    A program igyekszik ilyenkor minden hasznos információt átadni, azonban az általánosság miatt lehet, hogy pont az marad ki, amire szükségünk lenne.
                    <br><br>
                    A pontos "Találatok" résznél Ctrl+f kombinációval további kulcsszavas keresést végezhetünk.
                    <br><br>
                    Ha túl általános kulcsszót adunk meg, lehetséges, hogy a feltüntetett első 5-10 találat között nem lesz meg a konkrét információ amit keresünk.
                    <br><br>
                    <br><br>
                    A bal oldali példa esetében a válasz nem tartalmazza a vízbekötés díját. Ilyenkor jobb, ha a konkrét kérdést tesszük fel. (lásd 2. fül)
                </div>
                """,
                unsafe_allow_html=True
            )

    with tab2:
        st.markdown(
            "<div style='text-align: center;'>Példa keresés: Mennyibe kerül a vízbekötés?</div>",
            unsafe_allow_html=True
        )

        left2, right2 = st.columns(2)

        with left2:
            st.markdown("""<div>
                            <br>
                        </div>""", unsafe_allow_html=True)
            st.image(r"\user_manual\vizbekotes_dija_kereses.png")
        with right2:       
            st.markdown(
                """
                <div style='text-align: justify;'>
                    <br>
                    A konkrét kérdés megadásával a kulcsszón felül, annak a környezetét is beazonosítja a program, minél jobban leszűkítve a találatokat.
                    <br><br>
                    A program ilyenkor arra törekszik, hogy a konkrét kérdést válaszolja meg. Így pontosabb választ kapunk.
                    <br><br>
                    </div>
                """,
                unsafe_allow_html=True
            )

    with tab3:
        st.markdown(
            "<div style='text-align: center;'>Példa keresés: oltóvíz bekötés</div>",
            unsafe_allow_html=True
        )

        left3, right3 = st.columns(2)

        with left3:
            st.image(r"user_manual\oltoviz_kereses_jelentes.png")
            st.image(r"user_manual\oltoviz_kereses_jelentes_valasz1.png")
        with right3:       
            st.markdown(
                """
                <div style='text-align: justify;'>
                    <br><br>
                    Ez esetben bár mi tudjuk, hogy mit szeretnénk megtalálni, manuálisan a dokumentumokban egyszerű kulcsszavas kereséssel sokszor nem lehetséges. Például hiába keresünk locsolómérőre, ha az Üzletszabályzatban az locsolási célú mellékvízmérőként szerepel, vagy közműfejlesztésre, ha az a jogszabályi definíció szerint víziközmű-fejlesztés.
                    <br><br>
                    A kereső program úgy lett megtervezve, hogy ezekre a problémákra a válaszok felkínálása során figyeljen.
                    <br><br>
                    Jelen esetben "oltóvíz bekötés" témára keresve a tartalomjegyzék találatokban szerepel a tűzoltási célú ivóvízbekötés is.
                    <br>
                    A válaszok között fel van tüntetve az ivóvízbekötések során kikötött tűzoltást érintő feltételünk, valamint a kizárólag tűzoltási célú ivóvízbekötés leírása is.
                    </div>
                """,
                unsafe_allow_html=True
            )


    st.markdown("""<div style='text-align: justify;'>A keresések során javasolt a kérdések átfogalmazásával kisérletezni. Felhasználási céltól függően eltérhet, mikor melyik megoldás a legjobb. Azonban a pontatlan találatok esetén is a kereső program a felhasználói visszajelzések alapján tanítható, így a segítségetekkel fejleszthetjük a közös tudásbázisunkat.
                    <br><br>
                    Ehhez szíveskedjetek a megadott válasz alatti Helyes &#128077 és Helytelen &#128078 gombokat használni.
                </div>""", unsafe_allow_html=True)







    st.divider()
    st.header("Visszajelzés")
    st.write("Az applikáció értékelésének menete:")


    tab4, tab5, tab6 = st.tabs(["Megválaszolás", "Felhasználói értékelés", "Hibajelentés"])

    with tab4:
        left4, right4 = st.columns(2)

        with left4:
            st.markdown("""<div>
                            <br>
                        </div>""", unsafe_allow_html=True)
            st.image(r"user_manual\oltoviz_kereses_jelentes_feedback.png")
            st.image(r"user_manual\oltoviz_kereses_jelentes_feedback2.png")

        with right4:
            st.markdown(
                """
                <div style='text-align: justify;'>
                    <br><br>
                    Minden keresés esetén lehetőségünk van a megadott választ értékelni.
                    <br>
                    A Helyes &#128077 gomb megnyomásával a választ rögzítjük. Más felhasználók hasonló kereséseinél így az itt leírtak tartalmilag, megfogalmazásban és stílusban hasonlóak lesznek.
                    <br>
                    A Helytelen &#128078 gomb megnyomása esetén lehetőségünk adódik fejleszteni a program válaszát.
                    <br><br>
                    Utóbbi esetében ilyenkor az segít a fejlesztésben a legtöbbet, ha manuálisan megkeressük a dokumentumokban a helyes választ és bemásoljuk a felkínált szövegmezőbe.
                    <br>
                    Ha a helyes válasz nem található a dokumentumok között, az alábbi információk megadásával tudtok segíteni:
                    <br>- Melyik dokumentumban található a válasz. (Minél pontosabban, annál jobb)
                    <br>- Pontatlanság esetén megadjátok mely rész helyes, mely rész téves.
                    <br>- Ha fogalmazással kapcsolatos problémát találtok, a megadott szöveg átfogalmazásával lehet javítani a válasz stílusán.
                    <br>- Jelzitek a válasz mely része téves, hiányos, esetleg ellentmondó.
                    <br><br>
                    </div>
                """,
                unsafe_allow_html=True
            )        

        st.markdown("""<div style='text-align: justify;'>A program csak a feltöltött dokumentumokban található adatok alapján tud választ adni, általános információval a TRV-ről nem rendelkezik. Olyan információt megadni, ami a nyomtatványokban nem szerepel nem érdemes. Például a szakfelügyelet csak a szennyvízbekötéseknél kerül említésre, pedig tudjuk, hogy minden vezetékeinket érintő beruházásra előírjuk. Üzletszabályzatban, Árnyilvántartásban ez viszont nem szerepel, így a keresés minőségét ezzel az információval nem tudjuk javítani. Erre majd lesz külön rendszer kidolgozva.
                    </div>""", unsafe_allow_html=True)




    with tab5:
        st.markdown("""<div style='text-align: justify;'>A kereső program pontrendszerrel (&#128542&#128530&#x1F610&#x1F642&#x1F604) és szöveges kifejtéssel értékelhető.
                        <br>
                        Az adott pontszámot és a kifejtést csak a Küldés gomb megnyomását követően mentjük. A smiley választása önmagában nem ad visszajelzést, a Küldés gombot is meg kell nyomni utána. Kifejtés nem kötelező.
                        <br>
                        Módosításra, hozzáadásra bármikor van lehetőség.
                        <br><br>
                        Felhasználói fejlesztési javaslataitokat, kéréseiteket itt, vagy a hibajelentésnél jelezhetitek.
                    </div>""", unsafe_allow_html=True)

    with tab6:
        st.markdown("""Előfordulhatnak programtervezési hibák, mely esetében az applikáció hibaüzenetet ad, ami valahogy így néz ki:                                     
                    </div>""", unsafe_allow_html=True)    
        st.error('Ez egy error, engem kell kimásolni és a bal oldalt található "Hibajelentés" fülnél beilleszteni.') 
        st.markdown("""<div style='text-align: justify;'>Ilyenkor kérlek figyeljetek arra, hogy a teljes tartalmat küldjétek el a jelentésnél. Próbáljátok meg körülírni, hogy milyen lépések vezettek a hibaüzenet keletkezéséhez.                         
                    </div>""", unsafe_allow_html=True)
        st.markdown("""<div style='text-align: justify;'>
                        <br>
                        Ha olyan hibát találtok, hogy a keresés során nem jól működne a tartalomjegyzék, vagy elérési hely átirányítás, esetleg nem egyeznének a találatok a hozzájuk rendelt dokumentumok nevével, netán a program a leírtaktól eltérő cselekvést végez, a hibajelentéskor szíveskedjetek minél több információt megadni: pontosan mire kerestetek rá, a helytelen interakció leírása, mit csinál a helytelen cselekvés.                                  
                    </div>""", unsafe_allow_html=True)    
        st.markdown("""<div style='text-align: justify;'>
                        <br>
                        Előfordulhat, hogy az applikáció egyáltalán nem elérhető, vagy a keresés nem működik. Ez többek között lehet szerverhiba, kapacitás probléma, vagy a kereséshez szükséges kreditek elfogyása. Ha a Hibajelentés nem működik, az alábbi e-mail címre tudtok nekem írni:
                    </div>""", unsafe_allow_html=True)
        st.markdown("gaalpeter94@gmail.com")


    st.divider()
    st.header("Mi várható még?")
    st.write("""
    - Egyelőre csak olyan szabályzókban lehetséges a keresés, ami publikusan elérhető (vízmű honlapok).
    - A tartalomjegyzék találatok rákattintásakor még nem tudunk egyből a feltüntetett oldalszámra ugrani, azt manuálisan kell beütni.
    - A kereső program nem tárolja a korábbi kereséseket, így egymásra épülő, chat alapú információ lekérdezés még nem lehetséges.
    """)

