from google import genai

client = genai.Client(api_key="AIzaSyD_fplPXko-UpvZCHxRS8Jiwh5onMoOGd4")

models = client.models.list()

for m in models:
    print(m.name)


