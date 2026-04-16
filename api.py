from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from playwright.async_api import async_playwright
from playwright.sync_api import sync_playwright
import re

app = FastAPI(title="Belgian Law Brain API — Lois & Jurisprudence v9")

# ─────────────────────────────────────────────────────────────────────────────
# DICTIONNAIRE DES LOIS BELGES — NUMAC VÉRIFIÉS SUR JUSTEL
# Domaines couverts :
#   1. Droit du travail
#   2. Droit administratif
#   3. Droit commercial
#   4. Droit financier
#   5. Droit fiscal

# ─────────────────────────────────────────────────────────────────────────────

LOIS_CONNUES = {

    # ══════════════════════════════════════════════════════════════════════════
    # 1. DROIT DU TRAVAIL
    # ══════════════════════════════════════════════════════════════════════════

    "contrat_travail": {
        "numac": "1978070303",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=1978-08-22&numac_search=1978070303&page=1&lg_txt=F&caller=list&1978070303=0&trier=promulgation&view_numac=2013012289&fr=f&nm_ecran=1978070303&choix1=et&choix2=et",
        "titre": "Loi du 3 juillet 1978 relative aux contrats de travail (LCT)(Version Consolidée)",
        "domaine": "travail",
        "aliases": [
            "licenciement", "préavis", "contrat travail", "rupture contrat",
            "démission", "période essai", "contrat durée déterminée",
            "contrat durée indéterminée", "cdi", "cdd", "employé", "ouvrier",
            "maladie incapacité", "licenciement maladie", "salaire",
            "rémunération", "travailleur", "indemnité congé", "délai préavis",
            "licenciement abusif", "force majeure médicale", "salaire garanti",
            "chômage temporaire", "suspension contrat", "motif grave",
            "clause non-concurrence", "clause non concurrence",
            "contrat de travail"
        ]
    },

    "bien_etre_travail": {
        "numac": "1996012650",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=1996-09-18&numac_search=1996012650&page=1&lg_txt=F&caller=list&1996012650=0&trier=promulgation&view_numac=1978070303fx2013012289&fr=f&nm_ecran=1996012650&choix1=et&choix2=et",
        "titre": "Loi du 4 août 1996 relative au bien-être des travailleurs lors de l'exécution de leur travail(Version Consolidée)",
        "domaine": "travail",
        "aliases": [
            "harcèlement", "harcèlement moral", "harcèlement sexuel",
            "bien-être travail", "bien être travail", "violence travail",
            "risques psychosociaux", "sécurité travail", "prévention",
            "conseiller prévention", "cppt", "stress travail",
            "burn out", "burnout", "charge psychosociale"
        ]
    },

    "duree_travail": {
        "numac": "1971031602",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=1971-03-30&numac_search=1971031602&page=1&lg_txt=F&caller=list&1971031602=0&trier=promulgation&view_numac=1996012650fx1978070303fx2013012289&fr=f&nm_ecran=1971031602&choix1=et&choix2=et",
        "titre": "Loi du 16 mars 1971 sur le travail",
        "domaine": "travail",
        "aliases": [
            "durée travail", "heures travail", "temps travail",
            "heures supplémentaires", "repos compensatoire", "travail nuit",
            "travail dimanche", "38 heures", "semaine travail",
            "travail enfants", "travail jeunes", "congé repos",
            "jours fériés", "repos hebdomadaire"
        ]
    },

    "statut_unique": {
        "numac": "2013012289",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2013-12-31&numac_search=2013012289&page=1&lg_txt=F&caller=list&2013012289=0&trier=promulgation&view_numac=1971031602fx1996012650fx1978070303fx2013012289&fr=f&nm_ecran=2013012289&choix1=et&choix2=et",
        "titre": "Loi du 26 décembre 2013 concernant l'introduction d'un statut unique entre ouvriers et employés",
        "domaine": "travail",
        "aliases": [
            "statut unique", "préavis harmonisé", "préavis ouvrier",
            "préavis employé", "loi statut unique", "harmonisation préavis",
            "jour carence", "carence", "ancienneté préavis",
            "préavis semaines", "préavis ancienneté"
        ]
    },

    "protection_maternite": {
        "numac": "1971031602",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=1971-03-30&numac_search=1971031602&page=1&lg_txt=F&caller=list&1971031602=0&trier=promulgation&view_numac=2013012289fx1971031602fx1996012650fx1978070303fx2013012289&fr=f&nm_ecran=1971031602&choix1=et&choix2=et",
        "titre": "Protection de la maternité — Loi du 16 mars 1971 (consolidée)",
        "domaine": "travail",
        "aliases": [
            "maternité", "congé maternité", "grossesse licenciement",
            "protection maternité", "allaitement travail",
            "congé naissance", "congé parental", "congé paternité",
            "protection grossesse", "femme enceinte licenciement"
        ]
    },

    "conges_annuels": {
        "numac": "1971062850",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=1971-09-30&numac_search=1971062850&page=1&lg_txt=F&caller=list&1971062850=0&trier=promulgation&view_numac=1971031602fx2013012289fx1971031602fx1996012650fx1978070303fx2013012289&fr=f&nm_ecran=1971062850&choix1=et&choix2=et",
        "titre": "Lois coordonnées du 28 juin 1971 relatives aux vacances annuelles des travailleurs salariés",
        "domaine": "travail",
        "aliases": [
            "vacances annuelles", "congés payés", "pécule vacances",
            "double pécule", "congé annuel", "jours congé",
            "pécule de départ", "vacances travailleurs"
        ]
    },

    "travail_interimaire": {
        "numac": "1987012597",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=1987-08-20&numac_search=1987012597&page=1&lg_txt=F&caller=list&1987012597=0&trier=promulgation&view_numac=1971062850fx1971031602fx2013012289fx1996012650fx1978070303fx2013012289&fr=f&nm_ecran=1987012597&choix1=et&choix2=et",
        "titre": "Loi du 24 juillet 1987 sur le travail temporaire, le travail intérimaire et la mise de travailleurs à la disposition d'utilisateurs",
        "domaine": "travail",
        "aliases": [
            "temps partiel", "travail partiel", "mi-temps",
            "travail intérimaire", "interim", "intérim",
            "mise à disposition", "travail temporaire", "agence interim"
        ]
    },

    "protection_licenciement": {
        "numac": "2014201545",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2014-03-20&numac_search=2014201545&page=1&lg_txt=F&caller=list&2014201545=0&trier=promulgation&view_numac=1987012597fx1971062850fx1971031602fx2013012289fx1996012650fx1978070303fx2013012289&fr=f&nm_ecran=2014201545&choix1=et&choix2=et",
        "titre": "CCT n°109 du 12 février 2014 concernant la motivation du licenciement",
        "domaine": "travail",
        "aliases": [
            "licenciement déraisonnable", "motivation licenciement",
            "cct 109", "raison licenciement", "justification licenciement",
            "licenciement injustifié", "indemnité licenciement abusif"
        ]
    },

    "teletravail": {
        "numac": "2021A01165",  
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2021-05-05&numac_search=2021A01165&page=1&lg_txt=F&caller=list&2021A01165=1&trier=promulgation&view_numac=2021200888&fr=f&text1=CCT+149+&choix1=et&choix2=et",
        "titre": "CCT n°149 du 26 janvier 2021 concernant le télétravail (Version Coordonnée)",
        "domaine": "travail",
        "aliases": [
            "télétravail", "travail à domicile", "remote work",
            "travail hors entreprise", "cct 149", "accord télétravail",
            "droit à la déconnexion", "équipement télétravail"
        ]
    },

    "outplacement": {         #deja dans qdrant à verifier apres
        "numac": "2001012748", 
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2001-12-11&numac_search=2001012748&page=1&lg_txt=F&caller=list&2001012748=0&trier=promulgation&view_numac=2021200888fx2014201545fx1987012597fx1971062850fx1971031602fx2013012289fx1996012650fx1978070303fx2013012289&fr=f&nm_ecran=2001012748&choix1=et&choix2=et",
        "titre": "CCT n°82 du 10 juillet 2002 relative au droit à l'outplacement",
        "domaine": "travail",
        "aliases": [
            "outplacement", "reclassement professionnel",
            "accompagnement reclassement", "droit outplacement",
            "cct 82", "offre outplacement"
        ]
    },
    "statut_independants": {
        "numac": "1967072702",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=1967-07-29&numac_search=1967072702&page=1&lg_txt=F&caller=list&1967072702=0&trier=promulgation&view_numac=1978070303&ddd=1967-07-27&fr=f&choix1=et&choix2=et",
        "titre": "Arrêté royal n°38 du 27 juillet 1967 organisant le statut social des travailleurs indépendants",
        "domaine": "travail",
        "aliases": [
            "indépendant", "cotisations sociales indépendant",
            "statut social indépendant", "caisse assurances sociales",
            "gérant indépendant", "travailleur indépendant cotisation",
            "ar 38", "ar n 38", "ar n°38", "inasti",
            "revenu de remplacement indépendant",
            "pension indépendant", "maladie indépendant",
            "cotisations inasti", "cotisation trimestrielle indépendant",
            "statut social gérant", "indépendant à titre principal",
            "indépendant à titre complémentaire"
        ]
    },
    "anti_discrimination": {
        "numac": "2007002099",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2007-05-30&numac_search=2007002099&page=1&lg_txt=F&caller=list&2007002099=0&trier=promulgation&view_numac=2021a01165fx2021200888&fr=f&nm_ecran=2007002099&choix1=et&choix2=et",
        "titre": "Loi du 10 mai 2007 tendant à lutter contre certaines formes de discrimination",
        "domaine": "travail",
        "aliases": [
            "discrimination", "anti-discrimination", "égalité traitement",
            "discrimination raciale", "discrimination âge", "discrimination handicap",
            "discrimination religion", "discrimination sexe", "inégalité",
            "discrimination origine", "discrimination conviction",
            "discrimination orientation sexuelle"
        ]
    },

    "egalite_hommes_femmes": {
        "numac": "2007002098",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2007-05-30&numac_search=2007002098&page=1&lg_txt=F&caller=list&2007002098=0&trier=promulgation&view_numac=2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=2007002098&choix1=et&choix2=et",
        "titre": "Loi du 10 mai 2007 tendant à lutter contre la discrimination entre hommes et femmes",
        "domaine": "travail",
        "aliases": [
            "égalité hommes femmes", "discrimination genre",
            "paiement moins que les collègues masculins",
            "écart salarial", "pay gap", "sexisme travail",
            "inégalité salariale", "discrimination femme travail",
            "salaire inférieur femme", "salaire inférieur collègues masculins",
            "moins payée que collègues hommes", "rémunération inférieure femme",
            "inégalité de traitement femme homme", "discrimination salariale femme",
            "salaire homme femme", "écart de rémunération",
            "même travail salaire différent", "travail égal salaire inégal"
        ]
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 2. DROIT ADMINISTRATIF
    # ══════════════════════════════════════════════════════════════════════════

    "lois_coordonnees_conseil_etat": {
        "numac": "1973011250",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=1973-03-21&numac_search=1973011250&page=1&lg_txt=F&caller=list&1973011250=0&trier=promulgation&view_numac=2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=1973011250&choix1=et&choix2=et",
        "titre": "Lois coordonnées du 12 janvier 1973 sur le Conseil d'État",
        "domaine": "administratif",
        "aliases": [
            "conseil d'état", "recours administratif", "annulation acte administratif",
            "suspension acte", "recours en annulation", "recours conseil état",
            "arrêt conseil état", "chambre administrative", "contentieux administratif",
            "légalité acte administratif"
        ]
    },

    "loi_motivation_actes": {
        "numac": "1991000416",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=1991-09-12&numac_search=1991000416&page=1&lg_txt=F&caller=list&1991000416=0&trier=promulgation&view_numac=1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=1991000416&choix1=et&choix2=et",
        "titre": "Loi du 29 juillet 1991 relative à la motivation formelle des actes administratifs",
        "domaine": "administratif",
        "aliases": [
            "motivation acte administratif", "motivation formelle",
            "obligation motivation administration", "acte non motivé",
            "décision administrative sans motivation", "explication décision administrative"
        ]
    },

    "publicite_administration": {
        "numac": "1994000357",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=1994-06-30&numac_search=1994000357&page=1&lg_txt=F&caller=list&1994000357=0&trier=promulgation&view_numac=1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=1994000357&choix1=et&choix2=et",
        "titre": "Loi du 11 avril 1994 relative à la publicité de l'administration",
        "domaine": "administratif",
        "aliases": [
            "publicité administration", "accès documents administratifs",
            "transparence administrative", "demande documents publics",
            "droit accès administration", "documents administratifs",
            "accès information administration", "openness administration"
        ]
    },

    "marches_publics": {
        "numac": "2016021053",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2016-07-14&numac_search=2016021053&page=1&lg_txt=F&caller=list&2016021053=0&trier=promulgation&view_numac=1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=2016021053&choix1=et&choix2=et",
        "titre": "Loi du 17 juin 2016 relative aux marchés publics",
        "domaine": "administratif",
        "aliases": [
            "marchés publics", "appel d'offres", "adjudication",
            "soumission marché public", "cahier des charges",
            "pouvoir adjudicateur", "offre régulière", "attribution marché",
            "procédure négociée", "procédure ouverte", "procédure restreinte",
            "concession services", "partenariat public privé",
            "marché public travaux", "marché public fournitures",
            "marché public services"
        ]
    },

    "secrets_affaires": {
        "numac": "2018031595",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2018-08-14&numac_search=2018031595&page=1&lg_txt=F&caller=list&2018031595=0&trier=promulgation&view_numac=2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=2018031595&choix1=et&choix2=et",
        "titre": "30 JUILLET 2018. - Loi relative à la protection des secrets d'affaires",
        "domaine": "administratif",
        "aliases": [
            "recours marché public", "standstill marché public",
            "suspension attribution marché", "recours offre évincée",
            "contestation marché public"
        ]
    },

    "fonctionnaires_federaux": {
        "numac": "1937100201",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=1937-10-08&numac_search=1937100201&page=1&lg_txt=F&caller=list&1937100201=0&trier=promulgation&view_numac=2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=1937100201&choix1=et&choix2=et",
        "titre": "Arrêté royal du 2 octobre 1937 portant le statut des agents de l'État",
        "domaine": "administratif",
        "aliases": [
            "fonctionnaire", "agent de l'état", "statut fonctionnaire",
            "agent contractuel administration", "disciplinaire fonctionnaire",
            "licenciement fonctionnaire", "suspension fonctionnaire",
            "évaluation fonctionnaire", "grade fonctionnaire",
            "nomination fonctionnaire", "démission fonctionnaire"
        ]
    },

   "cpas": {
        "numac": "1976070810", 
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=1976-08-05&numac_search=1976070810&page=1&lg_txt=F&caller=list&1976070810=0&trier=promulgation&view_numac=1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=1976070810&choix1=et&choix2=et",
        "titre": "8 JUILLET 1976. - Loi organique des CPAS (Version Wallonne Consolidée)",
        "domaine": "administratif",
        "aliases": [
            "cpas", "aide sociale", "revenu intégration",
            "aide sociale urgente", "centre action sociale",
            "bénéficiaire cpas", "aide médicale urgente",
            "admission cpas", "projet individuel intégration"
        ]
    },

    "permis_urbanisme": {
        "numac": "2016A05561",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2016-11-14&numac_search=2016A05561&page=1&lg_txt=F&caller=list&2016A05561=0&trier=promulgation&view_numac=1976070810fx1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=2016A05561&choix1=et&choix2=et",
        "titre": "Code wallon du Développement territorial (CoDT) — Décret du 20 juillet 2016",
        "domaine": "administratif",
        "aliases": [
            "permis urbanisme", "permis construire", "permis lotir",
            "permis démolir", "infraction urbanistique", "codt",
            "certificat urbanisme", "recours permis", "affectation zone",
            "plan secteur", "revenu cadastral urbanisme",
            "régularisation infraction", "permis unique wallon"
        ]
    },
    

    "permis_environnement": {
        "numac": "1999027439",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=1999-06-08&numac_search=1999027439&page=1&lg_txt=F&caller=list&1999027439=0&trier=promulgation&view_numac=2016a05561fx1976070810fx1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=1999027439&choix1=et&choix2=et",
        "titre": "Décret wallon du 11 mars 1999 relatif au permis d'environnement",
        "domaine": "administratif",
        "aliases": [
            "permis environnement", "établissement classé",
            "nuisances sonores voisinage", "nuisances olfactives",
            "classe 1 2 3", "déclaration environnementale",
            "recours permis environnement", "autorisation exploiter"
        ]
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 3. DROIT COMMERCIAL
    # ══════════════════════════════════════════════════════════════════════════

    "code_societes": {
        "numac": "2019A40586",
        "url_source": " https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2019-04-04&numac_search=2019A40586&page=1&lg_txt=F&caller=list&2019A40586=0&trier=promulgation&view_numac=1999027439fx2016a05561fx1976070810fx1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=2019A40586&choix1=et&choix2=et",
        "titre": "Code des sociétés et des associations du 23 mars 2019 (CSA/WVV)",
        "domaine": "commercial",
        "aliases": [
            "société", "csa", "wvv", "sprl", "bv", "srl", "sa", "nv",
            "administrateur", "gérant", "assemblée générale",
            "responsabilité dirigeant", "faillite société",
            "dissolution société", "liquidation", "révocation gérant",
            "révocation administrateur", "mandat gérant", "gérant statutaire",
            "associé", "actionnaire", "parts sociales", "actions",
            "capital social", "statuts société", "scrl", "asbl",
            "fondation", "organe administration", "conseil administration",
            "responsabilité administrateur", "action en responsabilité",
            "résolution conflits associés", "exclusion associé",
            "retrait associé"
        ]
    },

    "insolvabilite": {
        "numac": "2017012998",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2017-09-11&numac_search=2017012998&page=1&lg_txt=F&caller=list&2017012998=0&trier=promulgation&view_numac=2019a40586fx1999027439fx2016a05561fx1976070810fx1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=2017012998&choix1=et&choix2=et",
        "titre": "Code de droit de l'insolvabilité (Livre XX CDE) — Loi du 11 août 2017",
        "domaine": "commercial",
        "aliases": [
            "faillite", "insolvabilité", "réorganisation judiciaire",
            "concordat", "curateur", "débiteur insolvable",
            "procédure collective", "liquidation judiciaire",
            "aveu faillite", "déconfiture", "remise dette",
            "plan de remboursement", "préfaillite", "prj",
            "procédure en réorganisation judiciaire",
            "accord amiable", "transfert sous autorité judiciaire",
            "sonnette d'alarme", "dissolution judiciaire"
        ]
    },

    "code_droit_economique": {
        "numac": "2013A11134",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2013-03-29&numac_search=2013A11134&page=1&lg_txt=F&caller=list&2013A11134=0&trier=promulgation&view_numac=2017012998fx2019a40586fx1999027439fx2016a05561fx1976070810fx1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=2013A11134&choix1=et&choix2=et",
        "titre": "28 FEVRIER 2013 Code de droit économique (CDE)",
        "domaine": "commercial",
        "aliases": [
            "pratiques commerce", "concurrence déloyale", "publicité trompeuse",
            "protection consommateur", "clause abusive", "contrat consommation",
            "droit économique", "vente consommateur", "garantie légale",
            "droit de rétractation", "e-commerce", "vente en ligne",
            "publicité comparative", "prime fidélité",
            "droit commercial général"
        ]
    },

    "agence_commerciale": {
        "numac": "2013A11134",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2013-03-29&numac_search=2013A11134&page=1&lg_txt=F&caller=list&2013A11134=0&trier=promulgation&view_numac=2017012998fx2019a40586fx1999027439fx2016a05561fx1976070810fx1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=2013A11134&choix1=et&choix2=et",
        "titre": "Code de droit économique - Livre X (Agence commerciale)",
        "domaine": "commercial",
        "aliases": [
            "agent commercial", "contrat agence", "agence commerciale",
            "indemnité clientèle", "résiliation agence",
            "commission agent", "exclusivité territoire",
            "préavis agent commercial", "contrat agent"
        ]
    },

    "franchise": {
        "numac": "2013A11134",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2013-03-29&numac_search=2013A11134&page=1&lg_txt=F&caller=list&2013A11134=0&trier=promulgation&view_numac=2017012998fx2019a40586fx1999027439fx2016a05561fx1976070810fx1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=2013A11134&choix1=et&choix2=et",
        "titre": "Code de Droit Économique (CDE) - Livre X 'Accords de coopération commerciale'",
        "domaine": "commercial",
        "aliases": [
            "franchise", "franchisé", "franchiseur",
            "accord partenariat commercial", "document information précontractuel",
            "contrat franchise", "redevance franchise", "résiliation franchise",
            "information précontractuelle franchise"
        ]
    },

    "contrats_commerciaux_b2b": {
        "numac": "2019011404",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2019-05-24&numac_search=2019011404&page=1&lg_txt=F&caller=list&2019011404=0&trier=promulgation&view_numac=2013a11134fx2017012998fx2019a40586fx1999027439fx2016a05561fx1976070810fx1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=2019011404&choix1=et&choix2=et",
        "titre": "Loi du 4 avril 2019 modifiant le Code de droit économique — clauses abusives B2B",
        "domaine": "commercial",
        "aliases": [
            "clause abusive b2b", "clause noire b2b", "clause grise b2b",
            "contrat entre entreprises", "déséquilibre manifeste b2b",
            "pratique déloyale entreprise", "abus dépendance économique"
        ]
    },

    "propriete_intellectuelle": {
        "numac": "2013A11134",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2013-03-29&numac_search=2013A11134&page=1&lg_txt=F&caller=list&2013A11134=0&trier=promulgation&view_numac=2017012998fx2019a40586fx1999027439fx2016a05561fx1976070810fx1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=2013A11134&choix1=et&choix2=et",
        "titre": "Code de droit économique — Livre XI : Propriété intellectuelle",
        "domaine": "commercial",
        "aliases": [
            "propriété intellectuelle", "droit auteur", "droits auteur",
            "copyright", "brevet", "marque", "droit voisin",
            "œuvre intellectuelle", "logiciel droit", "base de données droit",
            "dessin modèle", "propriété industrielle", "innovation travail"
        ]
    },

    "droit_auteur": {
        "numac": "2013A11134",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2013-03-29&numac_search=2013A11134&page=1&lg_txt=F&caller=list&2013A11134=0&trier=promulgation&view_numac=2017012998fx2019a40586fx1999027439fx2016a05561fx1976070810fx1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=2013A11134&choix1=et&choix2=et",
        "titre": "Code de droit économique - Livre XI (Propriété intellectuelle)",
        "domaine": "commercial",
        "aliases": [
            "droits auteur salarié", "œuvre créée travail", "auteur employé",
            "droits auteur contrat travail", "cession droits auteur",
            "droit moral auteur", "droits patrimoniaux auteur"
        ]
    },

    "bail_commercial": {
        "numac": "1951043003",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&lg_txt=f&cn_search=2019041328",
        "titre": "Loi du 30 avril 1951 sur les baux commerciaux",
        "domaine": "commercial",
        "aliases": [
            "bail commercial", "bail fonds commerce", "renouvellement bail commercial",
            "indemnité éviction", "droit renouvellement",
            "loyer commercial", "cession bail commercial"
        ]
    },
     "retard_paiement": {
        "numac": "2002009716",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2002-08-07&numac_search=2002009716&page=1&lg_txt=F&caller=list&2002009716=0&trier=promulgation&view_numac=1967072702fx1978070303&fr=f&nm_ecran=2002009716&choix1=et&choix2=et",
        "titre": "Loi du 2 août 2002 concernant la lutte contre le retard de paiement dans les transactions commerciales",
        "domaine": "commercial",
        "aliases": [
            "retard paiement", "facture impayée", "intérêts retard",
            "paiement en retard", "délai paiement", "facture non payée",
            "indemnité recouvrement", "intérêts de retard commercial",
            "paiement b2b", "créancier impayé", "débiteur défaillant",
            "40 euros frais recouvrement", "taux intérêt retard",
            "transaction commerciale retard", "facture échue",
            "recouvrement créance commerciale", "intérêts légaux facture"
        ]
    },
    "pratiques_marche": {
        "numac": "2013A11134",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2013-03-29&numac_search=2013A11134&page=1&lg_txt=F&caller=list&2013A11134=0&trier=promulgation&view_numac=2017012998fx2019a40586fx1999027439fx2016a05561fx1976070810fx1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=2013A11134&choix1=et&choix2=et",
        "titre": "Code de droit économique — Livre VI : Pratiques du marché",
        "domaine": "commercial",
        "aliases": [
            "soldes", "liquidation commerciale", "vente perte",
            "prime vente", "loterie commerciale", "jeu concours",
            "action promotionnelle", "publicité mensongère",
            "indication prix", "comparaison prix"
        ]
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 4. DROIT FINANCIER
    # ══════════════════════════════════════════════════════════════════════════

    "loi_fsma": {
        "numac": "2002003392",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2002-09-04&numac_search=2002003392&page=1&lg_txt=F&caller=list&2002003392=0&trier=promulgation&view_numac=2019011404fx2013a11134fx2017012998fx2019a40586fx1999027439fx2016a05561fx1976070810fx1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=2002003392&choix1=et&choix2=et",
        "titre": "Loi du 2 août 2002 relative à la surveillance du secteur financier et aux services financiers",
        "domaine": "financier",
        "aliases": [
            "fsma", "surveillance financière", "services financiers",
            "intermediaire financier", "délit d'initié", "manipulation marché",
            "abus marché", "prospectus", "information privilégiée",
            "insider trading", "intégrité marché financier"
            
        ]
    },

    "banques_loi": {
        "numac": "2014003194",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2014-05-07&numac_search=2014003194&page=1&lg_txt=F&caller=list&2014003194=0&trier=promulgation&view_numac=2002003392fx2019011404fx2013a11134fx2017012998fx2019a40586fx1999027439fx2016a05561fx1976070810fx1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=2014003194&choix1=et&choix2=et",
        "titre": "Loi du 25 avril 2014 relative au statut et au contrôle des établissements de crédit (loi bancaire)",
        "domaine": "financier",
        "aliases": [
            "banque", "établissement crédit", "agrément bancaire",
            "dépôt bancaire", "secret bancaire", "saisie compte bancaire",
            "garantie dépôts", "fonds protection dépôts",
            "contrôle bnb banque", "résolution bancaire",
            "bail-in banque"
        ]
    },

    "credit_consommateur": {
        "numac": "2013A11134",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2013-03-29&numac_search=2013A11134&page=1&lg_txt=F&caller=list&2013A11134=0&trier=promulgation&view_numac=2017012998fx2019a40586fx1999027439fx2016a05561fx1976070810fx1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=2013A11134&choix1=et&choix2=et",
        "titre": "Code de droit économique - Livre VII (Crédit consommateur )",
        "domaine": "financier",
        "aliases": [
            "crédit consommateur", "prêt personnel", "crédit voiture",
            "taux annuel effectif global", "taeg", "teg",
            "contrat crédit consommation", "résiliation crédit",
            "remboursement anticipé crédit", "centrale des crédits",
            "surendettement", "règlement collectif dettes", "médiateur dettes"
        ]
    },

    "credit_hypothecaire": {
        "numac": "2013A11134",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2013-03-29&numac_search=2013A11134&page=1&lg_txt=F&caller=list&2013A11134=0&trier=promulgation&view_numac=2017012998fx2019a40586fx1999027439fx2016a05561fx1976070810fx1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=2013A11134&choix1=et&choix2=et",
        "titre": "Code de droit économique - Livre VII (Crédit hypothécaire)",
        "domaine": "financier",
        "aliases": [
            "crédit hypothécaire", "prêt immobilier", "hypothèque bancaire",
            "taux hypothécaire", "remboursement anticipé hypothèque",
            "mainlevée hypothèque", "saisie immeuble", "vente forcée immeuble",
            "défaillance emprunteur", "contrat prêt immobilier",
            "évaluation bien immobilier crédit"
        ]
    },

    "assurances": {
        "numac": "2014011239",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2014-04-30&numac_search=2014011239&page=1&lg_txt=F&caller=list&2014011239=0&trier=promulgation&view_numac=2014003194fx2002003392fx2019011404fx2013a11134fx2017012998fx2019a40586fx1999027439fx2016a05561fx1976070810fx1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=2014011239&choix1=et&choix2=et",
        "titre": "Loi du 4 avril 2014 relative aux assurances",
        "domaine": "financier",
        "aliases": [
            "assurance", "contrat assurance", "prime assurance",
            "sinistre", "déclaration sinistre", "indemnisation assurance",
            "exclusion garantie", "résiliation assurance",
            "assurance vie", "assurance incendie", "assurance auto",
            "assurance responsabilité", "assureur", "assuré",
            "courtier assurance", "police assurance", "franchise assurance"
        ]
    },

    "services_paiement": {
        "numac": "2018030643",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2018-03-26&numac_search=2018030643&page=1&lg_txt=F&caller=list&2018030643=0&trier=promulgation&view_numac=2014011239fx2014003194fx2002003392fx2019011404fx2013a11134fx2017012998fx2019a40586fx1999027439fx2016a05561fx1976070810fx1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=2018030643&choix1=et&choix2=et",
        "titre": "Loi du 11 mars 2018 relative au statut et au contrôle des établissements de paiement et des établissements de monnaie électronique (PSD2)",
        "domaine": "financier",
        "aliases": [
            "paiement électronique", "virement bancaire", "prélèvement automatique",
            "établissement paiement", "monnaie électronique", "psd2",
            "accès compte bancaire tiers", "open banking", "agrégateur bancaire",
            "remboursement virement non autorisé"
        ]
    },

    "blanchiment": {
        "numac": "2017013368",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2017-10-06&numac_search=2017013368&page=1&lg_txt=F&caller=list&2017013368=0&trier=promulgation&view_numac=2018030643fx2014011239fx2014003194fx2002003392fx2019011404fx2013a11134fx2017012998fx2019a40586fx1999027439fx2016a05561fx1976070810fx1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=2017013368&choix1=et&choix2=et",
        "titre": "Loi du 18 septembre 2017 relative à la prévention du blanchiment de capitaux et du financement du terrorisme",
        "domaine": "financier",
        "aliases": [
            "blanchiment", "blanchiment capitaux", "financement terrorisme",
            "ctif", "déclaration suspicion", "vigilance client",
            "know your customer", "kyc", "bénéficiaire effectif",
            "aml", "anti-blanchiment", "lutte blanchiment"
        ]
    },

    "instruments_financiers": {
        "numac": "2017014203",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=2017-12-07&numac_search=2017014203&page=1&lg_txt=F&caller=list&2017014203=0&trier=promulgation&view_numac=2017013368fx2018030643fx2014011239fx2014003194fx2002003392fx2019011404fx2013a11134fx2017012998fx2019a40586fx1999027439fx2016a05561fx1976070810fx1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=2017014203&choix1=et&choix2=et",
        "titre": "Loi du 21 novembre 2017 relative aux infrastructures des marchés d'instruments financiers (MiFID II)",
        "domaine": "financier",
        "aliases": [
            "mifid", "mifid2", "instruments financiers", "actions obligations",
            "fonds placement", "portefeuille valeurs", "conseil investissement",
            "gestion portefeuille", "test adéquation", "profil investisseur",
            "société bourse", "courtier bourse", "produit structuré",
            "dérivé financier", "produit financier complexe"
        ]
    },

    # ══════════════════════════════════════════════════════════════════════════
    # 5. DROIT FISCAL
    # ══════════════════════════════════════════════════════════════════════════

    "cir92": {
        "numac": "1992003456",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=1992-07-30&numac_search=1992003456&page=1&lg_txt=F&caller=list&1992003456=0&trier=promulgation&view_numac=2017014203fx2017013368fx2018030643fx2014011239fx2014003194fx2002003392fx2019011404fx2013a11134fx2017012998fx2019a40586fx1999027439fx2016a05561fx1976070810fx1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=1992003456&choix1=et&choix2=et",
        "titre": "Code des impôts sur les revenus 1992 (CIR92)",
        "domaine": "fiscal",
        "aliases": [
            "impôt revenus", "ipp", "isoc", "précompte professionnel",
            "déclaration fiscale", "déduction fiscale", "tax shift",
            "revenu imposable", "avantage nature", "frais professionnels",
            "voiture société", "chèques repas", "bonus salarial",
            "impôt personnes physiques", "impôt sociétés",
            "bénéfice imposable", "perte fiscale", "report pertes",
            "précompte mobilier", "dividende", "intérêt obligataire",
            "plus-value taxation", "revenus fonciers", "loyer imposable"
        ]
    },

    "tva": {
        "numac": "1969070305",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&sum_date=&pd_search=1969-07-17&numac_search=1969070305&page=1&lg_txt=F&caller=list&1969070305=0&trier=promulgation&view_numac=1992003456fx2017014203fx2017013368fx2018030643fx2014011239fx2014003194fx2002003392fx2019011404fx2013a11134fx2017012998fx2019a40586fx1999027439fx2016a05561fx1976070810fx1937100201fx2018031595fx2016021053fx1994000357fx1991000416fx1973011250fx2007002098fx2007002099fx2021a01165fx2021200888&fr=f&nm_ecran=1969070305&choix1=et&choix2=et",
        "titre": "3 JUILLET 1969. - Code de la taxe sur la valeur ajoutée (TVA)",
        "domaine": "fiscal",
        "aliases": [
            "tva", "taxe valeur ajoutée", "assujetti tva",
            "déclaration tva", "facture tva", "taux tva",
            "exonération tva", "remboursement tva", "autoliquidation",
            "numéro tva", "assujettissement tva", "tva mixte",
            "prorata tva", "tva cocontractant", "listing clients"
        ]
    },

    "droits_enregistrement": {
        "numac": "2021040322",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/rech.pl?language=fr&view_numac=2021040322",
        "titre": "Code des droits d'enregistrement, d'hypothèque et de greffe",
        "domaine": "fiscal",
        "aliases": [
            "droits enregistrement", "droits mutation", "frais notaire",
            "enregistrement acte", "droit de donation",
            "abattement droits enregistrement",
            "réduction droits enregistrement habitation propre",
            "portabilité", "chèque habitat"
        ]
    },

    "droits_succession": {
        "numac": "2006027130",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/rech.pl?language=fr&view_numac=2006027130",
        "titre": "Code des droits de succession (wallon : Décret du 19 janvier 2017)",
        "domaine": "fiscal",
        "aliases": [
            "droits succession", "impôt succession", "héritage fiscal",
            "déclaration succession", "actif successoral", "passif succession",
            "exonération succession", "taux succession",
            "transmission entreprise", "plan successoral",
            "donation avant décès", "réserve héréditaire fiscale"
        ]
    },

    "taxe_circulation": {
        "numac": "2020020547",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/rech.pl?language=fr&view_numac=2020020547",
        "titre": "Loi relative à la taxe de circulation sur les véhicules automobiles (coordonnée 1992)",
        "domaine": "fiscal",
        "aliases": [
            "taxe circulation", "vignette voiture", "plaque immatriculation taxe",
            "taxe mise en circulation", "taxe annuelle véhicule",
            "déduction voiture société", "avantage tce", "cotisation co2"
        ]
    },

    "taxe_regionale_wallonne": {
        "numac": "1999027513",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/rech.pl?language=fr&view_numac=1999027513",
        "titre": "Décret wallon du 6 mai 1999 relatif à l'établissement, au recouvrement et au contentieux en matière de taxes régionales wallonnes",
        "domaine": "fiscal",
        "aliases": [
            "taxe régionale wallonne", "taxe immondices", "taxe déchets wallonie",
            "taxe eau wallonie", "redevance épuration",
            "recours taxe régionale", "réclamation taxe wallonne"
        ]
    },

    "procedure_fiscale": {
        "numac": "1999003180",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/rech.pl?language=fr&view_numac=1999003180",
        "titre": "Loi du 15 mars 1999 relative au contentieux en matière fiscale (anciennement AR 1919)",
        "domaine": "fiscal",
        "aliases": [
            "réclamation fiscale", "contentieux fiscal", "recours fiscal",
            "contrôle fiscal", "vérification comptabilité",
            "rectification imposition", "taxation d'office",
            "avis rectification", "amende fiscale", "intérêts moratoires",
            "prescription fiscale", "délai réclamation",
            "délai imposition", "tribunal première instance fiscal"
        ]
    },

    "prix_transfert": {
        "numac": "1992003456",
        "url_source": "https://www.ejustice.just.fgov.be/cgi_loi/rech.pl?language=fr&view_numac=1992003456",
        "titre": "CIR92 — Articles relatifs aux prix de transfert (art. 185 § 2 et 207/1)",
        "domaine": "fiscal",
        "aliases": [
            "prix transfert", "transfer pricing", "groupe sociétés fiscal",
            "bénéfice transféré", "arm's length", "transaction intra-groupe",
            "accord préalable prix transfert", "ruling fiscal prix transfert"
        ]
    },

    
}


# ─────────────────────────────────────────────────────────────────────────────
# FONCTIONS UTILITAIRES
# ─────────────────────────────────────────────────────────────────────────────

def construire_url_citation(numac: str) -> str:
    """
    URL Justel officielle — format view_numac vérifié et fonctionnel.
    https://www.ejustice.just.fgov.be/cgi_loi/rech.pl?language=fr&view_numac=NUMAC
    """
    return f"https://www.ejustice.just.fgov.be/cgi_loi/rech.pl?language=fr&view_numac={numac}"


async def bloquer_ressources(route):
    if route.request.resource_type in ["image", "font", "media"]:
        await route.abort()
    else:
        await route.continue_()

def bloquer_ressources_sync(route):
    if route.request.resource_type in ["image", "font", "media"]:
        route.abort()
    else:
        route.continue_()


def detecter_loi_par_sujet(sujet: str) -> list[dict]:
    sujet_lower = sujet.lower()
    candidats = []
    for cle, loi in LOIS_CONNUES.items():
        score = 0
        aliases_matches = []
        for alias in loi["aliases"]:
            if alias in sujet_lower:
                score += len(alias.split())
                aliases_matches.append(alias)
        if score > 0:
            candidats.append({
                "cle": cle,
                "numac": loi["numac"],
                "titre": loi["titre"],
                "domaine": loi.get("domaine", ""),
                "score": score,
                "aliases_matches": aliases_matches
            })
    candidats.sort(key=lambda x: x["score"], reverse=True)
    return candidats


async def extraire_articles_depuis_texte(texte: str, mots_cles: list[str]) -> list[dict]:
    texte = re.sub(r'\n{3,}', '\n\n', texte)
    blocs = re.split(r'(?=\bArt(?:icle)?\.?\s*\d)', texte)
    articles = []
    for bloc in blocs[:120]:
        art_match = re.match(r'\bArt(?:icle)?\.?\s*(\S+)', bloc)
        if not art_match:
            continue
        art_num = art_match.group(1).strip().rstrip('.')
        score = sum(1 for mot in mots_cles if mot in bloc.lower())
        if score >= 1:
            articles.append({
                "article": art_num,
                "texte": bloc.strip()[:1500],
                "score": score
            })
    articles.sort(key=lambda x: x["score"], reverse=True)
    return articles[:5]


async def scraper_loi_par_numac(numac: str, mots_cles: list[str] = None) -> dict:
    url = construire_url_citation(numac)
    mots_cles = mots_cles or []
    BASE_URL_JUSTEL = "https://www.ejustice.just.fgov.be"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            locale="fr-BE"
        )
        page = await context.new_page()
        await page.route("**/*", bloquer_ressources)
        try:
            await page.goto(url, wait_until="networkidle", timeout=45000)
            await page.wait_for_timeout(2000)
            texte = await page.inner_text("body")
            if len(texte) < 500 or "formulaire" in texte.lower()[:200]:
                url_fallback = f"{BASE_URL_JUSTEL}/cgi_loi/change_lg.pl?language=fr&la=F&table_name=loi&cn={numac}"
                await page.goto(url_fallback, wait_until="networkidle", timeout=30000)
                await page.wait_for_timeout(1500)
                texte = await page.inner_text("body")
            texte = re.sub(r'\n{3,}', '\n\n', texte)
            articles = []
            if mots_cles:
                mots_filtres = [m for m in mots_cles if len(m) > 3]
                articles = await extraire_articles_depuis_texte(texte, mots_filtres)
            await browser.close()
            return {
                "status": "ok",
                "numac": numac,
                "url_source": url,
                "texte_longueur": len(texte),
                "articles": articles
            }
        except Exception as e:
            await browser.close()
            return {"status": "erreur", "numac": numac, "detail": str(e)}


async def recherche_justel_fallback(sujet: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            locale="fr-BE"
        )
        page = await context.new_page()
        try:
            await page.goto(
                "https://www.ejustice.just.fgov.be/cgi/rech.pl?language=fr",
                wait_until="networkidle", timeout=20000
            )
            await page.evaluate(f"""
                const form = document.querySelector('form');
                if (form) {{
                    const input = document.querySelector('input[name="text1"]');
                    if (input) input.value = '{sujet}';
                    const typeSelect = document.querySelector('select[name="dt"]');
                    if (typeSelect) {{
                        for (let opt of typeSelect.options) {{
                            if (opt.text.trim().toLowerCase() === 'loi') {{
                                opt.selected = true; break;
                            }}
                        }}
                    }}
                    form.submit();
                }}
            """)
            await page.wait_for_url("**/rech_res.pl**", timeout=12000)
            await page.wait_for_timeout(3000)

            liens = await page.query_selector_all("a[href*='numac']")
            resultats = []
            numacs_vus = set()
            for lien in liens[:20]:
                href = await lien.get_attribute("href") or ""
                titre = (await lien.inner_text()).strip()
                numac_match = re.search(r"numac_search=(\w+)", href)
                if numac_match and titre and titre != numac_match.group(1):
                    numac = numac_match.group(1)
                    if numac in numacs_vus:
                        continue
                    numacs_vus.add(numac)
                    est_loi = any(m in titre.lower() for m in ["loi du", "loi relative", "loi sur", "loi portant"])
                    mots_sujet = [m for m in sujet.lower().split() if len(m) > 3]
                    score_titre = sum(1 for m in mots_sujet if m in titre.lower())
                    resultats.append({
                        "numac": numac,
                        "titre": titre[:200],
                        "url_source": construire_url_citation(numac),
                        "est_loi": est_loi,
                        "score_titre": score_titre
                    })

            resultats.sort(key=lambda x: (not x["est_loi"], -x["score_titre"]))
            await browser.close()

            if not resultats:
                return {
                    "status": "non_trouve",
                    "message": f"Aucune loi trouvée pour '{sujet}'.",
                    "loi": None
                }

            premier = resultats[0]
            return {
                "status": "ok",
                "source": "justel_scraping_fallback",
                "loi": {
                    "titre": premier["titre"],
                    "numac": premier["numac"],
                    "url_source": premier["url_source"]
                },
                "autres_candidats": [
                    {"titre": r["titre"], "numac": r["numac"], "url_source": r["url_source"]}
                    for r in resultats[1:3]
                ],
                "instruction_agent": (
                    f"Pour citer des articles : GET /loi/article?numac={premier['numac']}&article=XX. "
                    f"URL source : {premier['url_source']}"
                )
            }
        except Exception as e:
            await browser.close()
            return {
                "status": "erreur_fallback",
                "message": f"Recherche Justel impossible : {str(e)}",
                "loi": None
            }


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES API
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/loi/connue")
async def loi_connue_par_sujet(
    sujet: str = Query(..., description="Sujet juridique en langage naturel"),
    scrape: bool = Query(False, description="Si True, scrape aussi les articles pertinents")
):
    candidats = detecter_loi_par_sujet(sujet)

    if not candidats:
        return await recherche_justel_fallback(sujet)

    meilleur = candidats[0]
    numac = meilleur["numac"]
    url_source = construire_url_citation(numac)

    reponse = {
        "status": "ok",
        "source": "dictionnaire_lois_connues",
        "confiance": "haute" if meilleur["score"] >= 3 else "moyenne",
        "loi": {
            "titre": meilleur["titre"],
            "numac": numac,
            "domaine": meilleur.get("domaine", ""),
            "url_source": url_source,
            "aliases_matches": meilleur["aliases_matches"],
            "score_pertinence": meilleur["score"]
        },
        "autres_candidats": [
            {
                "titre": c["titre"],
                "numac": c["numac"],
                "domaine": c.get("domaine", ""),
                "url_source": construire_url_citation(c["numac"]),
                "score": c["score"]
            }
            for c in candidats[1:3]
        ],
        "articles": [],
        "instruction_agent": (
            f"Pour citer des articles verbatim : GET /loi/article?numac={numac}&article=XX. "
            f"URL source à citer : {url_source}"
        )
    }

    if scrape:
        mots = [m for m in sujet.lower().split() if len(m) > 3]
        resultat_scrape = await scraper_loi_par_numac(numac, mots)
        reponse["articles"] = resultat_scrape.get("articles", [])
        reponse["scrape_status"] = resultat_scrape.get("status")

    return reponse


@app.get("/loi/sujet")
async def loi_sujet_alias(sujet: str = Query(...), langue: str = Query("fr")):
    return await loi_connue_par_sujet(sujet=sujet)


@app.get("/loi/numac")
async def lire_loi_par_numac(
    numac: str = Query(...),
    mots_cles: str = Query(""),
    max_articles: int = Query(5)
):
    mots = [m.strip() for m in mots_cles.split(",") if len(m.strip()) > 2] if mots_cles else []
    resultat = await scraper_loi_par_numac(numac, mots)
    if resultat["status"] == "erreur":
        raise HTTPException(status_code=502, detail=f"Impossible de récupérer {numac} : {resultat.get('detail')}")
    return {
        "status": "ok",
        "numac": numac,
        "url_source": resultat["url_source"],
        "texte_longueur": resultat["texte_longueur"],
        "articles_extraits": len(resultat.get("articles", [])[:max_articles]),
        "articles": resultat.get("articles", [])[:max_articles],
        "note": "Texte récupéré en temps réel depuis ejustice.just.fgov.be (Justel)"
    }


@app.get("/loi/article")
async def lire_article_precis(
    numac: str = Query(...),
    article: str = Query(...),
    langue: str = Query("fr")
):
    url = construire_url_citation(numac)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            locale="fr-BE"
        )
        page = await context.new_page()
        await page.route("**/*", bloquer_ressources)
        try:
            await page.goto(url, wait_until="networkidle", timeout=45000)
            await page.wait_for_timeout(2000)
            texte = await page.inner_text("body")
            texte = re.sub(r'\n{3,}', '\n\n', texte)

            article_escape = re.escape(article)
            patterns = [
                rf"(Art\.?\s*{article_escape}[\.< \t].+?)(?=\n\s*Art\.?\s*\d|\Z)",
                rf"(Article\s+{article_escape}[\. ].+?)(?=\n\s*Art\.?\s*\d|\Z)",
            ]
            texte_art = None
            for pat in patterns:
                m = re.search(pat, texte, re.DOTALL | re.IGNORECASE)
                if m:
                    texte_art = m.group(1)[:3000].strip()
                    break

            await browser.close()

            if texte_art:
                return {
                    "status": "ok",
                    "numac": numac,
                    "article": article,
                    "texte_verbatim": texte_art,
                    "url_source": url,
                    "note": "Texte récupéré en temps réel depuis Justel (législation consolidée)"
                }
            else:
                return {
                    "status": "article_non_trouve",
                    "numac": numac,
                    "article": article,
                    "texte_verbatim": None,
                    "url_source": url,
                    "note": f"Article {article} introuvable dans {numac}. Consultez directement : {url}"
                }
        except Exception as e:
            await browser.close()
            raise HTTPException(status_code=500, detail=str(e))



# ─────────────────────────────────────────────────────────────────────────────
# JURISPRUDENCE — ENDPOINTS JUPORTAL
# ─────────────────────────────────────────────────────────────────────────────

class QueryModel(BaseModel):
    mot_cle: str

class UrlModel(BaseModel):
    url: str


@app.post("/scrape")
async def scrape_jurisprudence(query: QueryModel):
    """Recherche jurisprudence JuPortal par mot-clé. Retourne arrêts post-2019."""
    mot_cle = query.mot_cle
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.route("**/*", bloquer_ressources)
        try:
            await page.goto("https://juportal.be/moteur/formulaire", timeout=60000)
            await page.locator("input#texpression").fill(mot_cle)
            await page.locator("button[type='submit']:has-text('Rechercher')").first.click()
            await page.wait_for_timeout(3000)
            liens_elements = await page.locator("a[href*='ECLI']").all()
            resultats = []
            for lien in liens_elements:
                href = await lien.get_attribute("href")
                if href and "ECLI" in href:
                    url_propre = href.split("?")[0].split("#")[0]
                    match_ecli = re.search(r"(ECLI:BE:[A-Z]+:\d{4}:[A-Z0-9.]+)", url_propre)
                    match_annee = re.search(r"ECLI:BE:[A-Z]+:(\d{4}):", url_propre)
                    if match_ecli and match_annee:
                        ecli = match_ecli.group(1)
                        annee = int(match_annee.group(1))
                        if annee >= 2019:
                            type_doc = "ARRÊT" if ":ARR." in ecli else "DÉCISION"
                            resultats.append({
                                "ecli": ecli,
                                "annee": annee,
                                "type": type_doc,
                                "url": "https://juportal.be" + url_propre
                            })
            resultats_tries = sorted(resultats, key=lambda x: x["annee"], reverse=True)[:10]
            texte = f"--- RÉSULTATS POUR '{mot_cle}' (post-2019) ---\n"
            for i, r in enumerate(resultats_tries):
                texte += f"ARR{i+1}: [{r['type']}] ECLI={r['ecli']} | ANNÉE={r['annee']} | URL={r['url']}\n"
            await browser.close()
            return {"status": "success", "data": texte}
        except Exception as e:
            await browser.close()
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/lire_arret")
def lire_arret_complet(query: UrlModel):
    """Lit le texte intégral d'un arrêt JuPortal depuis son URL."""
    url = query.url
    if "juportal.be" not in url:
        raise HTTPException(status_code=400, detail="L'URL doit provenir de juportal.be")
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            page.route("**/*", bloquer_ressources_sync)
            page.goto(url)
            page.wait_for_timeout(2000)
            texte_complet = page.locator("body").inner_text()
            if len(texte_complet) > 10000:
                texte_limite = (
                    texte_complet[:5000]
                    + "\n\n[... PARTIE CENTRALE COUPÉE POUR ALLÉGER LA LECTURE ...]\n\n"
                    + texte_complet[-5000:]
                )
            else:
                texte_limite = texte_complet
            match_ecli = re.search(r"(ECLI:BE:[A-Z]+:\d{4}:[A-Z0-9.]+)", url)
            ecli_confirme = match_ecli.group(1) if match_ecli else "ECLI non détecté dans l'URL"
            reponse_finale = (
                f"ECLI DE CET ARRÊT : {ecli_confirme}\n"
                f"URL SOURCE : {url}\n\n"
                f"TEXTE DE L'ARRÊT:\n{texte_limite}"
            )
            browser.close()
            return {"status": "success", "data": reponse_finale}
        except Exception as e:
            if "browser" in locals():
                browser.close()
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/loi/liste")
async def lister_lois_connues(domaine: str = Query("", description="Filtrer par domaine : travail, administratif, commercial, financier, fiscal, civil, social, pénal, transversal")):
    lois_filtrees = {
        cle: loi for cle, loi in LOIS_CONNUES.items()
        if not domaine or loi.get("domaine", "") == domaine
    }
    return {
        "status": "ok",
        "total": len(lois_filtrees),
        "filtre_domaine": domaine or "tous",
        "lois": [
            {
                "cle": cle,
                "titre": loi["titre"],
                "domaine": loi.get("domaine", ""),
                "numac": loi["numac"],
                "url_source": construire_url_citation(loi["numac"]),
                "nb_aliases": len(loi["aliases"])
            }
            for cle, loi in lois_filtrees.items()
        ]
    }


@app.get("/loi/debug")
async def debug_justel(sujet: str = Query(...)):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            locale="fr-BE"
        )
        page = await context.new_page()
        try:
            await page.goto("https://www.ejustice.just.fgov.be/cgi/rech.pl?language=fr",
                            wait_until="networkidle", timeout=30000)
            await page.wait_for_timeout(2000)
            await page.evaluate(f"""
                const form = document.querySelector('form');
                if (form) {{
                    const input = document.querySelector('input[name="text1"]');
                    if (input) input.value = '{sujet}';
                    form.submit();
                }}
            """)
            await page.wait_for_url("**/rech_res.pl**", timeout=15000)
            await page.wait_for_load_state("networkidle", timeout=15000)
            await page.wait_for_timeout(4000)
            liens = await page.query_selector_all("a[href*='numac']")
            resultats = []
            numacs_vus = set()
            for lien in liens[:20]:
                href = await lien.get_attribute("href") or ""
                titre = (await lien.inner_text()).strip()
                numac_match = re.search(r"numac_search=(\w+)", href)
                if numac_match and titre:
                    numac = numac_match.group(1)
                    if numac not in numacs_vus:
                        numacs_vus.add(numac)
                        resultats.append({
                            "numac": numac,
                            "titre": titre[:200],
                            "url_source": construire_url_citation(numac)
                        })
            await browser.close()
            return {"total": len(resultats), "resultats": resultats}
        except Exception as e:
            await browser.close()
            raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    domaines = {}
    for loi in LOIS_CONNUES.values():
        d = loi.get("domaine", "autre")
        domaines[d] = domaines.get(d, 0) + 1
    return {
        "status": "online",
        "version": "v8.0 — 5 domaines : travail, administratif, commercial, financier, fiscal",
        "lois_dans_dictionnaire": len(LOIS_CONNUES),
        "couverture_par_domaine": domaines,
        "url_format": "https://www.ejustice.just.fgov.be/cgi_loi/article.pl?language=fr&..."
    }
