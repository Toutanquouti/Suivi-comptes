"""Convertit les fichiers Excel de tricount-extractor en opérations du Carnet de comptes, chiffrées.

Utilisation : python outils/tricount_vers_carnet.py <dossier_excel> <fichier_sortie>
Variables d'environnement : TRICOUNT_MOI (ton nom dans Tricount), TRICOUNT_PHRASE (phrase secrète).
Le dépôt est public : ce script n'affiche jamais de montant ni de nom dans les journaux.
"""
import base64, datetime, glob, hashlib, json, os, re, sys, unicodedata
from openpyxl import load_workbook
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITERATIONS = 200000
CATEGORIES = [
    ('restaurant', ['restau', 'bar', 'food', 'drink', 'repas', 'cafe', 'resto']),
    ('courses', ['grocer', 'course', 'supermarch', 'market']),
    ('logement', ['rent', 'loyer', 'housing', 'logement']),
    ('voyages', ['accommodation', 'hotel', 'hebergement', 'travel', 'voyage', 'holiday', 'vacance']),
    ('transport', ['transport', 'fuel', 'essence', 'taxi', 'train', 'car', 'parking', 'toll', 'peage']),
    ('loisirs', ['entertain', 'loisir', 'leisure', 'activit', 'sport', 'culture']),
    ('shopping', ['shop', 'achat']),
    ('sante', ['health', 'sante', 'pharma']),
    ('factures', ['utilit', 'bill', 'facture', 'energ']),
    ('cadeaux', ['gift', 'cadeau']),
]


def n(s):
    s = unicodedata.normalize('NFD', str(s if s is not None else ''))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')


def lignes(wb, *noms):
    for ws in wb.worksheets:
        if any(x in n(ws.title) for x in noms):
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                return []
            tete = [n(h) for h in rows[0]]
            return [dict(zip(tete, r)) for r in rows[1:] if any(v not in (None, '') for v in r)]
    return None


def col(rows, exacts, contient=()):
    cles = list(rows[0].keys()) if rows else []
    for e in exacts:
        if e in cles:
            return e
    for c in contient:
        for k in cles:
            if c in k:
                return k
    return None


def montant(v):
    if v is None or v == '':
        return None
    try:
        return abs(float(str(v).replace(' ', '').replace(' ', '').replace(',', '.')))
    except ValueError:
        return None


def date_iso(v):
    if isinstance(v, (datetime.datetime, datetime.date)):
        return v.strftime('%Y-%m-%d')
    s = str(v or '')
    m = re.match(r'(\d{4})-(\d{2})-(\d{2})', s)
    if m:
        return '-'.join(m.groups())
    m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', s)
    return f'{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}' if m else None


def categorie(v):
    t = n(v)
    for cible, mots in CATEGORIES:
        if any(m in t for m in mots):
            return cible
    return 'autres'


def diagnostic(wb, fichier, raison):
    print(f'::error::{os.path.basename(fichier)} : {raison}')
    for ws in wb.worksheets:
        tete = next(ws.iter_rows(values_only=True, max_row=1), ())
        print(f'  feuille « {ws.title} » : colonnes {[n(h) for h in tete]}')
    sys.exit(1)


def convertir(fichier, moi):
    wb = load_workbook(fichier, read_only=True, data_only=True)
    entrees, allocs, membres = lignes(wb, 'entr'), lignes(wb, 'alloc'), lignes(wb, 'member') or []
    if not entrees or allocs is None:
        diagnostic(wb, fichier, 'feuilles « entries » ou « allocations » introuvables')
    e_id = col(entrees, ['id', 'entry_id', 'uuid'], ['_id'])
    e_date = col(entrees, ['date', 'date_payment'], ['date', 'created'])
    e_desc = col(entrees, ['description', 'title', 'label'], ['descr', 'title', 'label'])
    e_cat = col(entrees, ['category'], ['categ'])
    e_type = col(entrees, ['type', 'type_transaction', 'entry_type'], ['type'])
    a_entree = col(allocs, ['entry_id', 'entry'], ['entry'])
    a_membre = col(allocs, ['member', 'member_name', 'membership', 'name'], ['member', 'name', 'particip'])
    a_montant = col(allocs, ['amount', 'share', 'amount_value'], ['amount', 'share', 'montant'])
    if not all([e_id, e_date, a_entree, a_membre, a_montant]):
        diagnostic(wb, fichier, 'colonnes attendues introuvables')
    # Mes identifiants : mon nom, et mes id dans la feuille des membres
    moi_n, mes_ids = n(moi), {n(moi)}
    if membres:
        m_id = col(membres, ['id', 'member_id', 'uuid'], ['_id'])
        m_nom = col(membres, ['display_name', 'name', 'alias', 'member'], ['name', 'alias'])
        for m in membres:
            if m_nom and n(m.get(m_nom)) == moi_n and m_id:
                mes_ids.add(n(m.get(m_id)))
    mes_parts = {}
    for a in allocs:
        if n(a.get(a_membre)) in mes_ids:
            v = montant(a.get(a_montant))
            if v:
                cle = n(a.get(a_entree))
                mes_parts[cle] = mes_parts.get(cle, 0) + v
    if allocs and not mes_parts:
        print(f'::error::{os.path.basename(fichier)} : ton nom (TRICOUNT_MOI) ne correspond à aucun participant ({len(membres)} membres). Écris-le exactement comme dans Tricount.')
        sys.exit(1)
    groupe = os.path.splitext(os.path.basename(fichier))[0]
    ops = []
    for i, e in enumerate(entrees):
        t = n(e.get(e_type)) if e_type else ''
        if any(x in t for x in ('reimburs', 'rembours', 'transfer', 'balance', 'settle')):
            continue
        part = mes_parts.get(n(e.get(e_id)))
        d = date_iso(e.get(e_date))
        if not part or not d:
            continue
        revenu = any(x in t for x in ('income', 'revenu'))
        desc = str(e.get(e_desc) or '').strip() if e_desc else ''
        ops.append({
            'id': 'tc-' + n(groupe)[:24] + '-' + (n(e.get(e_id)) or str(i))[:40],
            'type': 'revenu' if revenu else 'depense',
            'montant': round(part, 2),
            'categorie': 'autres-revenus' if revenu else categorie(e.get(e_cat) if e_cat else desc),
            'date': d,
            'note': (desc + ' · ' if desc else '') + 'Tricount',
            'cree': 0,
        })
    return ops


def main():
    dossier, sortie = sys.argv[1], sys.argv[2]
    moi, phrase = os.environ.get('TRICOUNT_MOI', '').strip(), os.environ.get('TRICOUNT_PHRASE', '')
    if not moi or len(phrase) < 8:
        print('::error::Ajoute les secrets TRICOUNT_MOI et TRICOUNT_PHRASE (8 caractères minimum).'); sys.exit(1)
    fichiers = sorted(glob.glob(os.path.join(dossier, '**', '*.xlsx'), recursive=True))
    if not fichiers:
        print('::error::Aucun fichier Excel produit par tricount-extractor. Vérifie le secret TRICOUNT_IDS.'); sys.exit(1)
    ops = []
    for f in fichiers:
        ops += convertir(f, moi)
    ops.sort(key=lambda o: (o['date'], o['id']))
    clair = json.dumps({'operations': ops}, ensure_ascii=False, sort_keys=True).encode()
    empreinte = hashlib.sha256(phrase.encode() + b'|' + clair).hexdigest()
    try:
        if json.load(open(sortie)).get('empreinte') == empreinte:
            print(f'{len(fichiers)} tricount(s), {len(ops)} opérations : rien de nouveau.'); return
    except (OSError, ValueError):
        pass
    paquet = json.loads(clair)
    paquet['genere'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    sel, iv = os.urandom(16), os.urandom(12)
    cle = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=sel, iterations=ITERATIONS).derive(phrase.encode())
    chiffre = AESGCM(cle).encrypt(iv, json.dumps(paquet, ensure_ascii=False).encode(), None)
    b64 = lambda b: base64.b64encode(b).decode()
    json.dump({'v': 1, 'iter': ITERATIONS, 'sel': b64(sel), 'iv': b64(iv), 'donnees': b64(chiffre), 'empreinte': empreinte}, open(sortie, 'w'))
    print(f'{len(fichiers)} tricount(s), {len(ops)} opérations publiées (chiffrées).')


if __name__ == '__main__':
    main()
