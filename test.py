import litellm

litellm.set_verbose = True  # Add this line

response = litellm.completion(
    model="fireworks_ai/accounts/eriktajti-a69f1e/deployedModels/my-lora-llama31-8b-b6df4d49",
    messages=[{"role": "user", "content": "Hello, how are you?"}],
    api_key="fw_3ZhhWY3zea3May74cgPSqU4r"
)

print(response)
