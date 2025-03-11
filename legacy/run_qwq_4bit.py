import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


def load_model_and_tokenizer():
    # Define the model name
    model_name = "Qwen/QwQ-32B-Preview"

    # Configure 4-bit quantization
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
        bnb_4bit_quant_type="nf4",  # You can also try "fp4"
    )

    print(f"Loading the model {model_name} with 4-bit quantization...")
    # Load the model with 4-bit quantization
    model = AutoModelForCausalLM.from_pretrained(
        model_name, quantization_config=quantization_config, device_map="auto"
    )

    print("Loading tokenizer...")
    # Load the tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)

    print("Model and tokenizer loaded successfully in 4-bit quantization!")
    return model, tokenizer


def generate_response(
    model,
    tokenizer,
    prompt,
    system_prompt="You are a helpful and harmless assistant. You are Qwen developed by Alibaba. You should think step-by-step.",
    max_new_tokens=256,
    temperature=0.7,
    top_p=0.9,
    stream=False,
):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )

    print("Tokenizing input...")
    inputs = tokenizer([text], return_tensors="pt").to(model.device)
    input_length = inputs.input_ids.shape[1]

    if not stream:
        print("Generating response...")
        with torch.no_grad():
            generated_ids = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
            )

        # Extract only the new tokens
        generated_ids = [output_ids[input_length:] for output_ids in generated_ids]

        response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        return response

    else:
        print("Generating streaming response...")
        # Stream tokens as they're generated
        full_response = ""
        generated_tokens = []

        # Setup for streamed generation
        with torch.no_grad():
            print("\nQwQ: ", end="", flush=True)

            # Initialize the generation of tokens
            current_input_ids = inputs.input_ids.clone()

            for _ in range(max_new_tokens):
                # Get next token prediction
                outputs = model(current_input_ids)
                next_token_logits = outputs.logits[:, -1, :]

                # Apply temperature
                if temperature > 0:
                    next_token_logits = next_token_logits / temperature

                # Apply top-p (nucleus) filtering
                if top_p < 1.0:
                    sorted_logits, sorted_indices = torch.sort(
                        next_token_logits, descending=True
                    )
                    cumulative_probs = torch.cumsum(
                        torch.nn.functional.softmax(sorted_logits, dim=-1), dim=-1
                    )

                    # Remove tokens with cumulative probability above the threshold
                    sorted_indices_to_remove = cumulative_probs > top_p
                    # Shift the indices to the right to keep also the first token above the threshold
                    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[
                        ..., :-1
                    ].clone()
                    sorted_indices_to_remove[..., 0] = 0

                    for batch_idx in range(next_token_logits.size(0)):
                        indices_to_remove = sorted_indices[batch_idx][
                            sorted_indices_to_remove[batch_idx]
                        ]
                        next_token_logits[batch_idx, indices_to_remove] = -float("Inf")

                # Sample from the filtered distribution
                probs = torch.nn.functional.softmax(next_token_logits, dim=-1)
                next_token = torch.multinomial(probs, num_samples=1)

                # Add the predicted token to the input for next iteration
                current_input_ids = torch.cat([current_input_ids, next_token], dim=-1)

                # Convert to token ID
                token_id = next_token.item()
                generated_tokens.append(token_id)

                # Stop if EOS token
                if token_id == tokenizer.eos_token_id:
                    break

                # Decode only the new token and print
                # Get the new text from this token
                new_text = tokenizer.decode(token_id, skip_special_tokens=True)
                if new_text:  # Some tokens might not produce visible text
                    print(new_text, end="", flush=True)
                    full_response += new_text

                # Check if we've reached some common ending patterns
                # (depending on the model's training format)
                if (
                    full_response.endswith("</final_assistant_response>")
                    or full_response.endswith("</assistant>")
                    or full_response.endswith("<|im_end|>")
                ):
                    break

        print()  # Add a newline at the end
        return full_response


def run_repl():
    print("=== QwQ Model Interactive REPL ===")
    print("Loading model and tokenizer...")

    # Load model and tokenizer once
    model, tokenizer = load_model_and_tokenizer()

    # Allow customizing the system prompt
    default_system_prompt = "You are a helpful and harmless assistant. You are Qwen developed by Alibaba. You should think step-by-step."
    print(f"\nDefault system prompt: {default_system_prompt}")
    custom_prompt = input(
        "Enter custom system prompt (or press Enter to use default): "
    )
    system_prompt = custom_prompt if custom_prompt.strip() else default_system_prompt

    # Allow customizing generation parameters
    try:
        max_new_tokens = int(input("Enter max_new_tokens (default 256): ") or 256)
        temperature = float(input("Enter temperature (default 0.7): ") or 0.7)
        top_p = float(input("Enter top_p (default 0.9): ") or 0.9)

        # Ask if user wants streaming
        stream_input = input("Enable token streaming? (y/n, default y): ").lower()
        stream = stream_input != "n"  # Default to True unless explicitly 'n'
    except ValueError:
        print("Invalid input, using default values.")
        max_new_tokens = 256
        temperature = 0.7
        top_p = 0.9
        stream = True

    print("\n=== Model ready for conversation ===")
    print("Type 'exit', 'quit', or 'q' to end the session")
    print("Type 'params' to adjust generation parameters")
    print("Type 'system' to change the system prompt")
    print(
        "Type 'stream' to toggle streaming mode (currently: "
        + ("enabled" if stream else "disabled")
        + ")"
    )
    print("Type your message and press Enter to chat with QwQ\n")

    # Main interaction loop
    while True:
        user_input = input("You: ")

        # Check for exit commands
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Exiting REPL. Goodbye!")
            break

        # Check for parameter adjustment
        elif user_input.lower() == "params":
            try:
                max_new_tokens = int(
                    input("Enter max_new_tokens (current: {}): ".format(max_new_tokens))
                    or max_new_tokens
                )
                temperature = float(
                    input("Enter temperature (current: {}): ".format(temperature))
                    or temperature
                )
                top_p = float(
                    input("Enter top_p (current: {}): ".format(top_p)) or top_p
                )

                # Update streaming setting
                stream_input = input(
                    f"Enable token streaming? (y/n, current: {'y' if stream else 'n'}): "
                ).lower()
                if stream_input in ("y", "n"):
                    stream = stream_input == "y"

                print(
                    f"Parameters updated: max_new_tokens={max_new_tokens}, temperature={temperature}, top_p={top_p}, streaming={'enabled' if stream else 'disabled'}"
                )
            except ValueError:
                print("Invalid input, parameters unchanged.")
            continue

        # Check for system prompt change
        elif user_input.lower() == "system":
            new_system_prompt = input(
                f"Current system prompt: {system_prompt}\nEnter new system prompt: "
            )
            if new_system_prompt.strip():
                system_prompt = new_system_prompt
                print(f"System prompt updated to: {system_prompt}")
            continue

        # Check for stream toggle
        elif user_input.lower() == "stream":
            stream = not stream
            print(f"Streaming mode {'enabled' if stream else 'disabled'}")
            continue

        # Generate and display response
        response = generate_response(
            model,
            tokenizer,
            user_input,
            system_prompt=system_prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            stream=stream,  # Use the stream parameter from settings
        )

        # If not streaming, need to print the response
        if not stream:
            print("\nQwQ:", response)

        print()  # Add an empty line for readability


if __name__ == "__main__":
    # Run the interactive REPL
    run_repl()

