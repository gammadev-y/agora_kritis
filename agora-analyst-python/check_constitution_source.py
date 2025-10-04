"""Check the constitution source and law records."""
import json
from lib.supabase_client import get_supabase_admin_client

supabase = get_supabase_admin_client()

# Check the source
print("=" * 80)
print("SOURCE RECORD:")
print("=" * 80)
source_response = supabase.table('sources').select('id, slug, type_id, translations, created_at').eq('id', 'd7eaa191-fd7b-48ef-9013-33579398d6ad').execute()
if source_response.data:
    source = source_response.data[0]
    print(f"ID: {source['id']}")
    print(f"Slug: {source['slug']}")
    print(f"Type ID: {source['type_id']}")
    print(f"Created: {source['created_at']}")
    print(f"\nTranslations:")
    print(json.dumps(source['translations'], indent=2))
else:
    print("Source not found")

print("\n" + "=" * 80)
print("LAW RECORDS WITH SLUG 'ttulo-iprincpios-gerais':")
print("=" * 80)
law_response = supabase.table('laws').select('id, slug, official_number, official_title, type_id, enactment_date, translations').eq('slug', 'ttulo-iprincpios-gerais').execute()
if law_response.data:
    for law in law_response.data:
        print(f"\nLaw ID: {law['id']}")
        print(f"Slug: {law['slug']}")
        print(f"Official Number: {law['official_number']}")
        print(f"Official Title: {law['official_title']}")
        print(f"Type ID: {law['type_id']}")
        print(f"Enactment Date: {law['enactment_date']}")
        print(f"Translations: {json.dumps(law.get('translations'), indent=2)}")
else:
    print("Law not found")

print("\n" + "=" * 80)
print("RELATED ARTICLES:")
print("=" * 80)
articles_response = supabase.table('article_versions').select('id, article_number, content, translations').eq('law_id', law_response.data[0]['id'] if law_response.data else '').limit(3).execute()
if articles_response.data:
    for article in articles_response.data:
        print(f"\nArticle: {article['article_number']}")
        print(f"Content preview: {article['content'][:200]}...")
        print(f"Has translations: {bool(article.get('translations'))}")
else:
    print("No articles found")
