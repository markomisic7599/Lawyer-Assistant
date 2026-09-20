"""Illustrative hub articles and demo subscribers.

Fictional but realistic Serbian market scenarios for the website demo.
Not legal advice — sample content only.
"""

from __future__ import annotations

from . import (
    ContentStatus,
    DocStatus,
    EditorialState,
    HubArticle,
    Industry,
    SourceRef,
    Subscriber,
)


def sample_articles() -> list[HubArticle]:
    return [
        HubArticle(
            id="hub-solar-eps",
            title="Novi poziv za solarne kapacitete iznad 50 MW: uslovi, rizici i rokovi",
            industries=[Industry.ENERGY, Industry.FDI, Industry.PROCUREMENT],
            status=ContentStatus.OPPORTUNITY,
            executive_summary=(
                "EPS je objavio javni poziv za saradnju sa proizvođačima koji raspolažu "
                "solarnim kapacitetima od najmanje 50 MW. Za kvalifikovane proizvođače "
                "to može biti novi kanal plasmana, uz uslove priključenja, balansne "
                "odgovornosti, cijene i ugovornih garancija."
            ),
            what_happened=(
                "Objavljen je javni poziv za dugoročnu saradnju sa proizvođačima električne "
                "energije iz solarnih elektrana. Minimalni kapacitet i uslovi učešća su "
                "javno dostupni; rok za prijavu je kratak."
            ),
            who_affected=(
                "Proizvođači sa solarnim kapacitetima ≥ 50 MW, investitori u RTB/operativnim "
                "fazama, i EPC/developeri koji razmatraju offtake strukture sa EPS-om."
            ),
            why_business_matters=(
                "Otvara novi offtake kanal i može uticati na bankabilnost projekta. Uslovi "
                "priključenja, balansne odgovornosti i garancije direktno utiču na "
                "isplativost i raspodjelu rizika."
            ),
            key_risks=[
                "Diskvalifikacija zbog neispunjenih formalnih uslova prijave",
                "Neusklađenost ugovornih garancija sa projektnim finansiranjem",
                "Rizik kašnjenja priključenja i balansne odgovornosti",
                "Nejasna indeksacija / formiranje cijene u dugom roku",
            ],
            deadline="Rok za prijavu: 30 dana od objave (provjeriti zvanični tekst poziva)",
            action_points=[
                "Provjeriti da li kapacitet i status projekta ispunjavaju minimalne uslove",
                "Mapirati uslove priključenja i balansne odgovornosti na Vaš model",
                "Uporediti offtake uslove sa postojećim PPA / merchant pretpostavkama",
                "Pripremiti listu diskvalifikacionih rizika prije prijave",
                "Uskladiti garancije sa zahtjevima kreditora, ako postoje",
            ],
            micro_delivery=(
                "Kompanije koje razmatraju učešće mogu zatražiti našu kratku check-listu "
                "ključnih uslova i diskvalifikacionih rizika."
            ),
            sources=[
                SourceRef(
                    "Javni poziv — EPS (primjer)",
                    "https://example.com/eps-solar-call",
                    published="2026-09-10",
                    doc_status=DocStatus.IN_FORCE,
                )
            ],
            urgency=85,
            reliability=0.9,
            published_at="2026-09-12",
            editorial=EditorialState.PUBLISHED,
            claims_to_verify=["Tačan rok i minimalni kapacitet u zvaničnom tekstu poziva"],
        ),
        HubArticle(
            id="hub-vertical-rules",
            title="Nova pravila o vertikalnim sporazumima: koje ugovore distributeri moraju prilagoditi?",
            industries=[Industry.RETAIL, Industry.LIFE_SCIENCES, Industry.FDI],
            status=ContentStatus.IMPORTANT,
            executive_summary=(
                "Nova pravila o vertikalnim / distributivnim sporazumima mijenjaju okvir "
                "za postojeće mreže. Kompanije sa aktivnim distributivnim ugovorima "
                "treba da mapiraju izloženost prije roka usklađivanja."
            ),
            what_happened=(
                "Objavljena su nova pravila koja uređuju vertikalne sporazume. "
                "Dio odredbi ima odloženu primjenu; postoji rok za usklađivanje "
                "postojećih ugovora."
            ),
            who_affected=(
                "Distributeri, proizvođači sa ekskluzivnim / selektivnim mrežama, "
                "FMCG i pharma kompanije sa ugovorima o distribuciji u Srbiji."
            ),
            why_business_matters=(
                "Neusklađeni ugovori mogu biti nevažeći ili izloženi intervenciji "
                "nadzornog organa. Rok forsira internu odluku: audit, re-papering "
                "ili restrukturiranje mreže."
            ),
            key_risks=[
                "Klauzule koje više nisu dozvoljene u postojećim ugovorima",
                "Rok usklađivanja i odgovornost za propust",
                "Utjecaj na cjenovne i teritorijalne odredbe",
            ],
            deadline="Rok usklađivanja: 6 mjeseci od stupanja na snagu (provjeriti)",
            action_points=[
                "Inventarisati aktivne distributivne ugovore",
                "Označiti klauzule koje nova pravila posebno pogađaju",
                "Prioritetizirati ugovore po vrijednosti i riziku",
                "Pripremiti plan re-paperinga prije roka",
            ],
            micro_delivery=(
                "Kompanije sa distributivnom mrežom mogu zatražiti naš pregled "
                "promjene na jednoj strani, sa fokusom na tri tačke koje najčešće "
                "zahtijevaju pažnju."
            ),
            sources=[
                SourceRef(
                    "Službeni glasnik — primjer",
                    "https://example.com/gazette-vertical",
                    published="2026-09-01",
                    doc_status=DocStatus.IN_FORCE,
                )
            ],
            urgency=75,
            reliability=0.85,
            published_at="2026-09-05",
            editorial=EditorialState.PUBLISHED,
        ),
        HubArticle(
            id="hub-mining-eia",
            title="EIA i dozvole za kritične minerale: šta investitori treba da provjere prije RTB faze",
            industries=[Industry.MINING, Industry.FDI, Industry.ENERGY],
            status=ContentStatus.STRATEGIC,
            executive_summary=(
                "Projekti kritičnih minerala u fazi prelaska na dozvole i finansiranje "
                "sreću se sa uskim grlima u EIA i institucijskom interfejsu. "
                "Pravilna sekvenca dozvola štiti rok i bankabilnost."
            ),
            what_happened=(
                "Niz projekata prelazi iz istraživanja u dozvole / ESIA. Javno dostupni "
                "signali ukazuju na duže rokove i pojačanu pažnju na društvene i "
                "ekološke uslove."
            ),
            who_affected=(
                "Exploration / mining kompanije, JV partneri, development banke i "
                "investitori koji ulaze u permitting fazu u Srbiji."
            ),
            why_business_matters=(
                "Kašnjenje dozvole direktno odlaže FID i finansiranje. Pogrešan redoslijed "
                "koraka stvara trošak i reputacioni rizik."
            ),
            key_risks=[
                "Nepotpuna dokumentacija EIA / javni uvid",
                "Konflikt lokalnih interesa i institucionalnog interfejsa",
                "Neusklađenost sa uslovima kreditora (ESDD)",
            ],
            deadline="",
            action_points=[
                "Mapirati sve dozvole i saglasnosti na kritičnoj putanji",
                "Provjeriti status EIA i rokove javnog uvida",
                "Uskladiti permitting plan sa pretpostavkama finansiranja",
                "Identifikovati organe koji drže proces i opcije eskalacije",
            ],
            micro_delivery=(
                "Investitori u ovoj fazi mogu zatražiti preliminarnu mapu dozvola "
                "i saglasnosti za tipičan mining projekat u Srbiji."
            ),
            sources=[
                SourceRef(
                    "Relevantni propisi o procjeni uticaja (primjer)",
                    "https://example.com/eia-framework",
                    doc_status=DocStatus.IN_FORCE,
                )
            ],
            urgency=55,
            reliability=0.8,
            published_at="2026-09-08",
            editorial=EditorialState.PUBLISHED,
        ),
        HubArticle(
            id="hub-guarantee-case",
            title="Vrhovni sud ograničio naplatu bankarske garancije: posljedice za izvođače i naručioce",
            industries=[Industry.INFRA, Industry.BANKING, Industry.PROCUREMENT],
            status=ContentStatus.CASE_LAW,
            executive_summary=(
                "Nova odluka Vrhovnog suda sužava uslove pod kojima naručilac može "
                "uspješno naplatiti bankarsku garanciju. Izvođači i banke treba da "
                "preispitaju tekstove garancija i procedure zahtjeva."
            ),
            what_happened=(
                "Vrhovni sud je u nedavnoj odluci pojasnio standarde dokazivanja "
                "i formalne uslove za naplatu garancije na zahtjev."
            ),
            who_affected=(
                "Izvođači radova, javni i privatni naručioci, banke koje izdaju "
                "garancije, i advokati na construction / procurement poslovima."
            ),
            why_business_matters=(
                "Mijenja pregovaračku poziciju oko performance / advance payment "
                "garancija i može uticati na tekuće sporove i nove ugovore."
            ),
            key_risks=[
                "Garancije sa nejasanim uslovima naplate",
                "Zahtjevi za naplatu bez dovoljne dokumentacije",
                "Neusklađenost FIDIC / ugovornih modela sa domaćom praksom",
            ],
            deadline="",
            action_points=[
                "Pregledati standardne tekstove bankarskih garancija",
                "Uskladiti procedure zahtjeva sa novim standardom dokazivanja",
                "Kod tekućih sporova: procijeniti uticaj odluke na strategiju",
            ],
            micro_delivery=(
                "Izvođači i naručioci mogu zatražiti naš kratak pregled "
                "tri pitanja koja treba provjeriti u tekstu garancije nakon odluke."
            ),
            sources=[
                SourceRef(
                    "Odluka Vrhovnog suda (primjer)",
                    "https://example.com/supreme-court-guarantee",
                    published="2026-08-20",
                    doc_status=DocStatus.IN_FORCE,
                )
            ],
            urgency=60,
            reliability=0.88,
            published_at="2026-08-25",
            editorial=EditorialState.PUBLISHED,
        ),
        HubArticle(
            id="hub-incentive-automation",
            title="Subvencije za automatizaciju proizvodnje: ko može učestvovati i koja dokumentacija je potrebna?",
            industries=[Industry.FDI, Industry.TECH, Industry.RETAIL],
            status=ContentStatus.OPPORTUNITY,
            executive_summary=(
                "Novi program podsticaja za automatizaciju može donijeti značajna "
                "sredstva inbound investitorima i domaćim proizvođačima, uz uslove "
                "intenziteta državne pomoći i dokumentacije."
            ),
            what_happened=(
                "Objavljen je program / poziv vezan za podsticaje automatizacije "
                "proizvodnje. Definisan je okvirni budžet i uslovi prijave."
            ),
            who_affected=(
                "Proizvodne kompanije koje planiraju CAPEX za automatizaciju, "
                "FDI projekti u ekspaziji, i CFO / investment timovi."
            ),
            why_business_matters=(
                "Može materijalno smanjiti trošak investicije — ali samo ako se "
                "ispune uslovi intenziteta i pravovremeno prikupi dokumentacija."
            ),
            key_risks=[
                "Neispunjenje uslova intenziteta državne pomoći",
                "Nepotpuna dokumentacija i propust roka",
                "Konflikt sa drugim paralelnih podsticajima",
            ],
            deadline="Rok prijave: 45 dana (provjeriti zvanični poziv)",
            action_points=[
                "Provjeriti da li projekat ulazi u kvalifikovane troškove",
                "Procijeniti intenzitet pomoći u odnosu na veličinu kompanije",
                "Pripremiti listu potrebne dokumentacije",
                "Uskladiti timeline CAPEX-a sa rokom poziva",
            ],
            micro_delivery=(
                "Kompanije koje razmatraju prijavu mogu zatražiti preliminarnu "
                "procjenu ispunjenosti uslova i listu dokumentacije."
            ),
            sources=[
                SourceRef(
                    "Javni poziv / program podsticaja (primjer)",
                    "https://example.com/automation-incentive",
                    published="2026-09-15",
                    doc_status=DocStatus.IN_FORCE,
                )
            ],
            urgency=70,
            reliability=0.82,
            published_at="2026-09-16",
            editorial=EditorialState.PUBLISHED,
        ),
        # Editorial queue samples (not yet published)
        HubArticle(
            id="hub-draft-grid",
            title="Izmjene pravila priključenja na mrežu: rok i uticaj na solarne projekte u razvoju",
            industries=[Industry.ENERGY],
            status=ContentStatus.URGENT_ALERT,
            executive_summary="Nacrt — čeka pravnu kontrolu.",
            what_happened="Najavljene izmjene procedura priključenja.",
            who_affected="Solar / wind developeri sa zahtjevima u toku.",
            why_business_matters="Može pomjeriti COD i uslove finansiranja.",
            key_risks=["Kratak rok prilagođavanja", "Nepotpuni zahtjevi"],
            deadline="Javna rasprava: 15 dana",
            action_points=[
                "Provjeriti status tekućeg zahtjeva",
                "Uporediti nacrt sa postojećom procedurom",
                "Pripremiti komentare za javnu raspravu",
            ],
            micro_delivery=(
                "Developeri mogu zatražiti kalendar rokova i check-listu "
                "dokumenata za priključenje."
            ),
            sources=[
                SourceRef(
                    "Nacrt izmjena (primjer)",
                    "https://example.com/grid-connection-draft",
                    published="2026-09-18",
                    doc_status=DocStatus.DRAFT,
                )
            ],
            urgency=90,
            reliability=0.7,
            published_at="",
            editorial=EditorialState.IN_REVIEW,
            claims_to_verify=[
                "Tačan tekst nacrta",
                "Da li rok od 15 dana važi za sve tipove priključenja",
            ],
        ),
        HubArticle(
            id="hub-reject-noise",
            title="Opšta vijest o rastu BDP-a",
            industries=[Industry.BANKING],
            status=ContentStatus.NOT_RELEVANT,
            executive_summary="Nije dovoljno konkretno za hub.",
            what_happened="Objavljena makroekonomska statistika.",
            who_affected="Široko, bez sektorskog action pointa.",
            why_business_matters="Nema jasan odgovor zašto bi pravna služba ovo čitala danas.",
            key_risks=[],
            deadline="",
            action_points=[],
            micro_delivery="",
            sources=[],
            urgency=10,
            reliability=0.9,
            editorial=EditorialState.REJECTED,
            claims_to_verify=[],
        ),
    ]


def sample_subscribers() -> list[Subscriber]:
    return [
        Subscriber(
            email="legal@miningco.example.com",
            name="Legal Director",
            company="Mining Co. Serbia",
            industries=[Industry.MINING, Industry.FDI],
        ),
        Subscriber(
            email="cfo@solardev.example.com",
            name="CFO",
            company="Solar Dev d.o.o.",
            industries=[Industry.ENERGY, Industry.PROCUREMENT],
        ),
        Subscriber(
            email="gc@fmcg.example.com",
            name="General Counsel",
            company="FMCG Distributor",
            industries=[Industry.RETAIL, Industry.LIFE_SCIENCES],
        ),
    ]


def articles_for_industries(
    articles: list[HubArticle], industries: list[Industry]
) -> list[HubArticle]:
    """Only published, non-rejected content matching any selected industry."""
    wanted = set(industries)
    return [
        a
        for a in articles
        if a.editorial == EditorialState.PUBLISHED
        and a.status != ContentStatus.NOT_RELEVANT
        and wanted.intersection(a.industries)
    ]
