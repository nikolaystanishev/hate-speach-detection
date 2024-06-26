import torch
from torch.nn import Module, Sequential, Linear
from transformers import BertModel, BertTokenizer, AutoModel
import torchvision.models as models
import os
import sys
import json
import clip
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM


class HateMemeModel(Module):

    def __init__(self, text_model, image_model, dropout=0.1):
        super(HateMemeModel, self).__init__()
        self.text_model = text_model
        self.batch_norm1 = torch.nn.BatchNorm1d(256)
        self.image_model = image_model
        self.batch_norm2 = torch.nn.BatchNorm1d(512)
        
        # 2816
        self.fc1 = Linear(256, 256)
        self.fc2 = Linear(512, 256)
        self.fc3 = Linear(256, 128)
        self.fc4 = Linear(128, 64)
        self.fc5 = Linear(64, 2)

        self.relu = torch.nn.PReLU()
        self.dropout = torch.nn.Dropout(dropout)

    def freeze_backbone_model(self):
        for param in self.text_model.named_parameters():
            # if 'layer.7' not in param[0] and 'pooler' not in param[0]:
            param[1].requires_grad = False
        for param in self.image_model.named_parameters():
            # if 'layer4' not in param[0]:
            param[1].requires_grad = False

    def forward(self, text, image):
        text_features = self.relu(self.batch_norm1(self.text_model(**text).pooler_output))
        image_features = self.image_model(image)
        image_features = self.relu(self.batch_norm2(image_features.view(image_features.size(0), -1)))

        text = self.relu(self.fc1(text_features))
        image = self.relu(self.fc2(image_features))
        combined = text * image
        out = self.dropout(self.relu(self.fc3(combined)))
        out = self.dropout(self.relu(self.fc4(out)))
        out = self.fc5(out)
        
        return out


class PretrainedModel:

    @staticmethod
    def load_bert_text_model():
        return AutoModel.from_pretrained("google/bert_uncased_L-4_H-256_A-4")
    
    @staticmethod
    def load_bert_tokenizer():
        return BertTokenizer.from_pretrained('bert-base-uncased')
    
    @staticmethod
    def load_resnet_image_model():
        model = models.resnet34(weights=models.ResNet34_Weights.DEFAULT)
        modules = list(model.children())[:-1]
        return Sequential(*modules)

    @staticmethod
    def load_clip_model(name="ViT-L/14"):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        return clip.load(name, device=device)

    @staticmethod
    def load_clip_tokenizer():
        return clip.tokenize
    
    @staticmethod
    def load_para_t5_model():
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        return AutoModelForSeq2SeqLM.from_pretrained("Vamsi/T5_Paraphrase_Paws").to(device)
    
    @staticmethod
    def load_t5_tokenizer():
        return AutoTokenizer.from_pretrained("Vamsi/T5_Paraphrase_Paws")  



class ClipHateMemeModelFreeze(Module):
        def __init__(self, size):
            super(ClipHateMemeModelFreeze, self).__init__()
            self.dropout0 = torch.nn.Dropout(0.2)

            self.relu = torch.nn.ReLU()

            self.projection_image = Sequential( 
                Linear(size[1], 1024),
            )
            self.projection_text = Sequential( 
                Linear(size[0], 1024),
            )
            
            self.text_image_net = Sequential(
                self.dropout0,
                Linear(1024, 1024),
                self.relu,
                self.dropout0,
                Linear(1024, 2),
            )




        def forward(self, text, image):

            text_projection = self.projection_text(text)
            image_projection = self.projection_image(image)
            image_projection = torch.nn.functional.normalize(image_projection, p=2, dim=0)
            text_projection = torch.nn.functional.normalize(text_projection, p=2, dim=0)                   



            text_image = torch.mul(image_projection, text_projection)


            out = self.text_image_net(text_image)

            return out
