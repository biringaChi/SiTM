import torch.nn as nn

class HCCD(nn.Module):
    def __init__(self):
        super(HCCD, self).__init__()
        self.nclasses = 9
        self.dprob = 0.5
            
        self.model = nn.Sequential(
            nn.Linear(768, 512),
            nn.LeakyReLU(), 
            nn.Dropout(self.dprob),
            nn.Linear(512, 256), 
            nn.LeakyReLU(),
            nn.Dropout(self.dprob),
            nn.Linear(256, self.nclasses)
        )
        
    def forward(self, x):
        return self.model(x)