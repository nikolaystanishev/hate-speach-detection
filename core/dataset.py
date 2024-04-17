import os
import json
from PIL import Image
import torch
from torch.utils.data import Dataset
from core.model import PretrainedModel
import clip
from tqdm.notebook import tqdm

class HatefulMemesDataset(Dataset):

    def __init__(self, data_file_path, tokenizer=None, transform=None):
        self.data = [json.loads(jline) for jline in open(data_file_path, 'r').readlines()]
        self.data_dir = os.path.dirname(data_file_path)
        self.tokenizer = tokenizer
        self.transform = transform

    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        el = self.data[idx]

        img = Image.open(os.path.join(self.data_dir, el['img']))
        text = el['text']
        label = el['label']

        if self.transform:
            img = self.transform(img)
        if self.tokenizer:
            text = self.tokenizer(text, return_tensors='pt')

        return img, text, label


def collate_fn(batch):
    lens = [len(row[1]['input_ids'][0]) for row in batch]
    bsz, max_seq_len = len(batch), max(lens)

    input_ids_tensor = torch.zeros(bsz, max_seq_len).long()
    token_type_ids_tensor = torch.zeros(bsz, max_seq_len).long()
    attention_mask_tensor = torch.zeros(bsz, max_seq_len).long()

    image_tensor = torch.stack([row[0] for row in batch])

    label_tensor = torch.tensor([row[2] for row in batch])

    for i_batch, (input_row, length) in enumerate(zip(batch, lens)):
        input_ids_tensor[i_batch, :length] = input_row[1]['input_ids'][0]
        token_type_ids_tensor[i_batch, :length] = input_row[1]['token_type_ids'][0]
        attention_mask_tensor[i_batch, :length] = input_row[1]['attention_mask'][0]

    return (
        image_tensor,
        {
            'input_ids': input_ids_tensor,
            'token_type_ids': token_type_ids_tensor,
            'attention_mask': attention_mask_tensor
        },
        label_tensor
    )

class ClipHatefulMemesDataset(Dataset):
    def __init__(self, data_file_path, tokenizer=None, transform=None):
        self.data = [json.loads(jline) for jline in open(data_file_path, 'r').readlines()]
        self.data_dir = os.path.dirname(data_file_path)
        self.tokenizer = tokenizer
        self.transform = transform

    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        el = self.data[idx]

        img = Image.open(os.path.join(self.data_dir, el['img']))
        text = el['text']
        label = el['label']

        if self.transform:
            img = self.transform(img)
        if self.tokenizer:
            text = self.tokenizer(text, context_length=77, truncate=True)

        return img, text, label

def collate_fn_clip(batch):
    lens = [len(row[1][0]) for row in batch]
    bsz, max_seq_len = len(batch), max(lens)
    input_ids_tensor = torch.zeros(bsz, max_seq_len).long()
    image_tensor = torch.stack([row[0] for row in batch])

    label_tensor = torch.tensor([row[2] for row in batch])

    for i_batch, (input_row, length) in enumerate(zip(batch, lens)):
        input_ids_tensor[i_batch, :length] = input_row[1]
    return (
        image_tensor,
        {
            'input_ids': input_ids_tensor,
        },
        label_tensor
    )

class ClipHatefulMemeDatasetFreeze(Dataset):
    def __init__(self, data_file_path):
        self.data = [json.loads(jline) for jline in open(data_file_path, 'r').readlines()]
        self.data_dir = os.path.dirname(data_file_path)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        el = self.data[idx]

        img = torch.tensor(el['img_embedding'][0]).to(self.device)
        text = torch.tensor(el['text_embedding'][0]).to(self.device)
        label = torch.tensor(el['label']).to(self.device)
        return img, text, label
