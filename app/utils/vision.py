from transformers import CLIPProcessor, CLIPModel, AutoProcessor, AutoModelForObjectDetection
from PIL import Image
import torch
from typing import List, Dict, Any, Tuple
import numpy as np
import requests
from io import BytesIO

class VisionAnnotator:
    def __init__(self):
        # Initialize CLIP model for image-text matching
        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        
        # Initialize object detection model
        self.detector_processor = AutoProcessor.from_pretrained("facebook/detr-resnet-50")
        self.detector_model = AutoModelForObjectDetection.from_pretrained("facebook/detr-resnet-50")
        
        # Move models to GPU if available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.clip_model.to(self.device)
        self.detector_model.to(self.device)
    
    def load_image(self, image_source: str) -> Image.Image:
        """Load image from URL or file."""
        if image_source.startswith(('http://', 'https://')):
            response = requests.get(image_source)
            image = Image.open(BytesIO(response.content))
        else:
            image = Image.open(image_source)
        return image.convert('RGB')
    
    def detect_regions(self, image: Image.Image) -> List[Dict[str, Any]]:
        """Detect regions in the image using DETR."""
        inputs = self.detector_processor(images=image, return_tensors="pt").to(self.device)
        outputs = self.detector_model(**inputs)
        
        # Convert outputs to bounding boxes
        target_sizes = torch.tensor([image.size[::-1]])
        results = self.detector_processor.post_process_object_detection(
            outputs, target_sizes=target_sizes, threshold=0.7
        )[0]
        
        regions = []
        for score, label, box in zip(results["scores"], results["labels"], results["boxes"]):
            regions.append({
                "x": box[0].item(),
                "y": box[1].item(),
                "width": (box[2] - box[0]).item(),
                "height": (box[3] - box[1]).item(),
                "confidence": score.item(),
                "label": self.detector_model.config.id2label[label.item()]
            })
        
        return regions
    
    def match_components(self, image: Image.Image, regions: List[Dict[str, Any]], 
                        component_descriptions: List[str]) -> List[Dict[str, Any]]:
        """Match detected regions to component descriptions using CLIP."""
        matched_regions = []
        
        for region in regions:
            # Crop the region from the image
            x, y, w, h = map(int, [region["x"], region["y"], region["width"], region["height"]])
            region_image = image.crop((x, y, x + w, y + h))
            
            # Process image and text with CLIP
            image_inputs = self.clip_processor(images=region_image, return_tensors="pt").to(self.device)
            text_inputs = self.clip_processor(text=component_descriptions, return_tensors="pt", padding=True).to(self.device)
            
            # Get embeddings
            image_features = self.clip_model.get_image_features(**image_inputs)
            text_features = self.clip_model.get_text_features(**text_inputs)
            
            # Normalize features
            image_features = image_features / image_features.norm(dim=1, keepdim=True)
            text_features = text_features / text_features.norm(dim=1, keepdim=True)
            
            # Calculate similarity
            similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
            
            # Get best match
            best_match_idx = similarity.argmax().item()
            best_match_score = similarity[0][best_match_idx].item()
            
            matched_regions.append({
                **region,
                "component_match": {
                    "name": component_descriptions[best_match_idx],
                    "confidence": best_match_score
                }
            })
        
        return matched_regions
    
    def annotate_image(self, image_source: str, component_descriptions: List[str]) -> Dict[str, Any]:
        """Annotate image with detected regions and matched components."""
        # Load image
        image = self.load_image(image_source)
        
        # Detect regions
        regions = self.detect_regions(image)
        
        # Match components
        matched_regions = self.match_components(image, regions, component_descriptions)
        
        # Build hierarchy
        hierarchy = self._build_hierarchy(matched_regions)
        
        return {
            "regions": matched_regions,
            "hierarchy": hierarchy
        }
    
    def _build_hierarchy(self, regions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build a hierarchical structure from the matched regions."""
        # Sort regions by y-coordinate to determine vertical stacking
        sorted_regions = sorted(regions, key=lambda r: r["y"])
        
        hierarchy = {
            "type": "root",
            "children": []
        }
        
        current_level = hierarchy
        current_y = 0
        
        for region in sorted_regions:
            # If there's a significant vertical gap, create a new level
            if region["y"] - current_y > 50:  # threshold for new level
                current_level = hierarchy
                current_y = region["y"]
            
            # Add region to current level
            current_level["children"].append({
                "type": "component",
                "name": region["component_match"]["name"],
                "confidence": region["component_match"]["confidence"],
                "region": {
                    "x": region["x"],
                    "y": region["y"],
                    "width": region["width"],
                    "height": region["height"]
                },
                "children": []
            })
            
            current_level = current_level["children"][-1]
        
        return hierarchy 