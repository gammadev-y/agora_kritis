"""Check the created law and its articles for issues."""
import json
from lib.supabase_client import get_supabase_admin_client

supabase = get_supabase_admin_client()
law_id = 'f606285b-1c03-4190-a37e-95d5830ef755'

print("=" * 80)
print("LAW RECORD:")
print("=" * 80)
law_response = supabase.table('laws').select('*').eq('id', law_id).execute()
if law_response.data:
    law = law_response.data[0]
    print(f"ID: {law['id']}")
    print(f"Official Number: {law['official_number']}")
    print(f"Official Title: {law['official_title']}")
    print(f"Type ID: {law['type_id']}")
    print(f"Category ID: {law['category_id']}")
    print(f"Enactment Date: {law['enactment_date']}")
    print(f"Tags: {json.dumps(law['tags'], indent=2)}")

print("\n" + "=" * 80)
print("LAW ARTICLES:")
print("=" * 80)
articles_response = supabase.table('law_articles').select('id, article_order, valid_from, translations, tags').eq('law_id', law_id).order('article_order').execute()
if articles_response.data:
    for article in articles_response.data:
        print(f"\nArticle {article['article_order']}:")
        print(f"  ID: {article['id']}")
        print(f"  Valid From: {article['valid_from']}")
        print(f"  Has Tags: {bool(article.get('tags'))}")
        print(f"  Tags: {json.dumps(article.get('tags', {}), indent=4)}")
        
        translations = article.get('translations', {})
        print(f"  Has Translations: {bool(translations)}")
        if translations:
            print(f"  Has PT: {'pt' in translations}")
            print(f"  Has EN: {'en' in translations}")
            if 'pt' in translations:
                print(f"    PT Summary: {translations['pt'].get('informal_summary', 'N/A')[:100]}...")
            if 'en' in translations:
                print(f"    EN Summary: {translations['en'].get('informal_summary', 'N/A')[:100]}...")
        else:
            print(f"  ⚠️ TRANSLATIONS ARE EMPTY!")
