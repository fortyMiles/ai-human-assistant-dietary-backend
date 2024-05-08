import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model_path = "~/content/drive/MyDrive/llama3_nutrition/Llama-3-8B-sft-lora-food-nutrition-5-epoch"
os.environ['TRANSFORMERS_CACHE'] = model_path
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.bfloat16,
)

tokenizer = AutoTokenizer.from_pretrained(model_path)

model.to(device)


def generate_answer(model, tokenizer, messages):
  input_ids = tokenizer.apply_chat_template(
      messages,
      add_generation_prompt=True,
      return_tensors="pt"
  ).to(model.device)

  terminators = [
      tokenizer.eos_token_id,
      tokenizer.convert_tokens_to_ids("<|eot_id|>")
  ]

  torch.backends.cuda.enable_mem_efficient_sdp(False)
  torch.backends.cuda.enable_flash_sdp(False)
  # https://github.com/Lightning-AI/litgpt/issues/327

  outputs = model.generate(
      input_ids,
      max_new_tokens=5000,
      eos_token_id=terminators,
      do_sample=False,
 #     early_stopping=False,
     temperature=1,
      top_p=1,
  )

  response = outputs[0][input_ids.shape[-1]:]

  return tokenizer.decode(response, skip_special_tokens=False)


def get_person_dialog(messages):
    return generate_answer(model, tokenizer, messages)


if __name__ == '__main__':
    messages = [
        {"role": "system", "content": "You are a helpful health and dietary assistant. You will give advice for their healthy diet."},
        {"role": "user", "content": "I am a 30-year old man and from China. I am 1.7 meters tall and weigh 70 kg. I want to lose weight. Can you give the choice of "
                                    "my today breatfast, lunch and dinner, give this as a list, thanks? You answer should only include the food name and the weight of the food."},
    ]
    print(get_person_dialog(messages))
