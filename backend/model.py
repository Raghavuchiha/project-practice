# C2P-CLIP Model - Complete Code
# No fine-tuning - just inference

import torch
import torch.nn as nn
from transformers import CLIPModel, CLIPProcessor
from PIL import Image

# =====================
# Step 1 - Model Class
# =====================
class C2PModel(nn.Module):
    def __init__(self, name='openai/clip-vit-large-patch14'):
        super(C2PModel, self).__init__()
        
        # Load CLIP model
        self.model = CLIPModel.from_pretrained(name)
        
        # Remove text parts - not needed
        del self.model.text_model
        del self.model.text_projection
        del self.model.logit_scale
        
        # Freeze CLIP weights - not training
        self.model.vision_model.requires_grad_(False)
        self.model.visual_projection.requires_grad_(False)
        
        # Add classifier layer - structure only
        self.model.layer = nn.Linear(768, 1)

    def encode_image(self, img):
        # Pass image through CLIP vision model
        vision_outputs = self.model.vision_model(pixel_values=img)
        
        # Get summary of whole image - 1024 numbers
        pooled_output = vision_outputs[1]
        
        # Convert 1024 to 768 numbers
        image_features = self.model.visual_projection(pooled_output)
        
        return image_features

    def forward(self, img):
        # Get 768 features from image
        image_embeds = self.encode_image(img)
        
        # Normalize features
        image_embeds = image_embeds / image_embeds.norm(p=2, dim=-1, keepdim=True)
        
        # Pass to classifier - get 1 score
        return self.model.layer(image_embeds)


# =====================
# Step 2 - Load Model
# =====================
print("Loading model...")
model = C2PModel(name='openai/clip-vit-large-patch14')

# =====================
# Step 3 - Load C2P Pretrained Weights
# =====================
state_dict = torch.load(
    "D:/project-practice/checkpoints/C2P_CLIP-GenImage_release_20250224.pth",
    map_location="cpu"
)
model.load_state_dict(state_dict, strict=False)
print("C2P weights loaded!")

# =====================
# Step 4 - Load FC Parameters
# =====================
fc_state = torch.load(
    "D:/project-practice/checkpoints/fc_parameters.pth",
    map_location="cpu"
)
model.model.layer.weight.data = fc_state['fc.weight']
model.model.layer.bias.data = fc_state['fc.bias']
print("FC parameters loaded!")

# =====================
# Step 5 - Set to Inference Mode
# =====================
model.eval()
print("Model ready!")