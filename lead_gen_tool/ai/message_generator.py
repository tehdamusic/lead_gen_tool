import openai

def generate_personalized_message(name: str, platform: str) -> str:
    prompt = f"Generate a short, friendly, and engaging outreach message for {name} on {platform} to discuss business opportunities."
    
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": prompt}]
    )
    
    return response["choices"][0]["message"]["content"]
