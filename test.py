from google import genai

# Replace with your actual API key
API_KEY = "AIzaSyBHl61dmyV0vOxcZyT0fh9oVYoxxGjDQ1o"

client = genai.Client(api_key=API_KEY)

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Explain FastAPI in 3 lines."
)

print(response.text)