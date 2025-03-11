import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

def run_inference(prompt, system_prompt=None):
    # Model name
    model_name = "Qwen/QwQ-32B-Preview"
    
    # Load model and tokenizer
    print("Loading model and tokenizer...")
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,  # Using BF16 as mentioned in the model card
        device_map="auto"  # Automatically manage device placement
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    # Create chat messages
    if system_prompt is None:
        system_prompt = "You are a helpful and harmless assistant. You are Qwen developed by Alibaba. You should think step-by-step."
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    # Apply chat template to format the input properly
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    # Tokenize the input
    print("Generating response...")
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)
    
    # Generate response
    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=512,  # Adjust as needed
        temperature=0.7,     # Controls randomness, adjust as needed
        top_p=0.9,           # Nucleus sampling parameter
        do_sample=True       # Use sampling rather than greedy decoding
    )
    
    # Extract only the new tokens (the response)
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]
    
    # Decode the response
    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    
    return response

if __name__ == "__main__":
    # Example usage
    user_prompt = "Explain quantum computing in simple terms."
    response = run_inference(user_prompt)
    print("\nUser: ", user_prompt)
    print("\nQwQ: ", response)
    
    # You can also try with a custom system prompt
    custom_system = "You are an expert in physics with a knack for simple explanations."
    custom_prompt = "How many r in strawberry?"
    response = run_inference(custom_prompt, custom_system)
    print("\nUser: ", custom_prompt)
    print("\nQwQ: ", response)
