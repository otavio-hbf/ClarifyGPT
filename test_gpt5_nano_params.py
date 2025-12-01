import os
import requests
import json

url = "https://api.openai.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
    "Content-Type": "application/json"
}

# Test each parameter individually
params_to_test = [
    {"temperature": 1.0},
    {"max_completion_tokens": 4000},
    {"frequency_penalty": 0},
    {"presence_penalty": 0},
    {"n": 1},
    {"top_p": 0.95},  # Should fail
]

base_data = {
    "model": "gpt-5-nano",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say 'test'."}
    ],
}

for param in params_to_test:
    test_data = {**base_data, **param}
    response = requests.post(url, headers=headers, json=test_data)
    result = response.json()
    
    param_name = list(param.keys())[0]
    if response.status_code == 200:
        print(f"✅ {param_name}: SUPPORTED")
    else:
        print(f"❌ {param_name}: NOT SUPPORTED")
        if 'error' in result:
            print(f"   Error: {result['error']['message']}")
    print()