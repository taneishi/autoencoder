import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.utils.data
import timeit
import sys

def load_dataset(batch_size, device):
    if len(sys.argv) < 2:
        sys.exit('no input filename')
    else:
        filename = sys.argv[1]

    # Load dataset
    train = np.load(filename, allow_pickle=True)
    train_y, train_x = train['labels'], train['data']
    test = np.load(filename.replace('train', 'test'), allow_pickle=True)
    test_y, test_x = test['labels'], test['data']

    print('train %d test %d' % (len(train_y), len(test_y)))

    # create torch tensor from numpy array
    train_x_torch = torch.FloatTensor(train_x).to(device)

    test_x_torch = torch.FloatTensor(test_x).to(device)

    train = torch.utils.data.TensorDataset(train_x_torch)
    test = torch.utils.data.TensorDataset(test_x_torch)

    train_dataloader = torch.utils.data.DataLoader(train, batch_size=batch_size, shuffle=False)
    test_dataloader = torch.utils.data.DataLoader(test, batch_size=batch_size, shuffle=False)

    return train_dataloader, test_dataloader

class AutoEncoder(nn.Module):
    
    def __init__(self):
        super(AutoEncoder, self).__init__()
        # encoder
        self.e1 = nn.Linear(1500, 1000)
        self.e2 = nn.Linear(1000, 500)
        self.e3 = nn.Linear(500, 250)
        # Latent View
        self.lv = nn.Linear(250, 100)
        # Decoder
        self.d1 = nn.Linear(100, 250)
        self.d2 = nn.Linear(250, 500)
        self.d3 = nn.Linear(500, 1000)
        self.output_layer = nn.Linear(1000, 1500)
        
    def forward(self,x):
        x = F.relu(self.e1(x))
        x = F.relu(self.e2(x))
        x = F.relu(self.e3(x))
        x = torch.sigmoid(self.lv(x))
        x = F.relu(self.d1(x))
        x = F.relu(self.d2(x))
        x = F.relu(self.d3(x))
        x = self.output_layer(x)
        return x

def train(dataloader, model, optimizer, loss_func, batch_size):
    model.train()
    train_loss = 0
    EPOCHS = 1000

    for epoch in range(EPOCHS):
        epoch_start = timeit.default_timer()
        for index, (data, ) in enumerate(dataloader, 1):
            optimizer.zero_grad()
            pred = model(data)
            loss = loss_func(pred, data)
            train_loss += loss.item()
            loss.backward() # backpropagation
            optimizer.step()
            print('\repoch %2d [%3d/%3d] train_loss %5.3f' % (epoch, index, len(dataloader), loss.item()), end='')
        print(' time %5.2f' % (timeit.default_timer() - epoch_start))

def test(dataloader, model):
    model.eval()
    predictions = []
    for data, in dataloader:
            pred = model(data)
            for prediction in pred:
                predictions.append(prediction)
    return predictions

def main():
    batch_size = 10

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print('Using %s device.' % device)

    train_dataloader, test_dataloader = load_dataset(batch_size, device)

    ae = AutoEncoder().to(device)
    print(ae)

    # define our optimizer and loss function
    loss_func = nn.MSELoss()
    optimizer = torch.optim.Adam(ae.parameters(), lr=1e-4)

    train(train_dataloader, ae, optimizer, loss_func, batch_size)

    predictions = test(test_dataloader, ae)
    print(len(predictions))

if __name__ == '__main__':
    main()
