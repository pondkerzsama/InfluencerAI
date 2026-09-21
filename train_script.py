import torch

print("Checking GPU Status...")
if torch.cuda.is_available():
    print("✅ Success! GPU is ready.")
    print(f"🎮 GPU Name: {torch.cuda.get_device_name(0)}")
else:
    print("❌ Failed. Using CPU only.")