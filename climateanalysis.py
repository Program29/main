import torch 
import torchvision 
import torchvision.transforms as transforms 
from torch.autograd import Variable 
import torch.nn as nn 
import torch.nn.functional as F 
import math 
import sys 
from tqdm import tqdm 
 
 
BATCH_SIZE = 64 
 
 
class RBM(nn.Module): 
    ''' 
    This class defines all the functions needed for an BinaryRBN model 
    where the visible and hidden units are both considered binary 
    ''' 
 
 
    def __init__(self, 
                visible_units=256, 
                hidden_units = 64, 
                k=2, 
                learning_rate=1e-5, 
                learning_rate_decay = False, 
                xavier_init = False, 
                increase_to_cd_k = False, 
                use_gpu = False 
                ): 
        ''' 
        Defines the model 
        W:Wheights shape (visible_units,hidden_units) 
        c:hidden unit bias shape (hidden_units , ) 
        b : visible unit bias shape(visisble_units ,) 
        ''' 
        super(RBM,self).__init__() 
        self.desc = "RBM" 
 
 
        self.visible_units = visible_units 
        self.hidden_units = hidden_units 
        self.k = k 
        self.learning_rate = learning_rate 
        self.learning_rate_decay = learning_rate_decay 
        self.xavier_init = xavier_init 
        self.increase_to_cd_k = increase_to_cd_k 
        self.use_gpu = use_gpu 
        self.batch_size = 16 
 
 
 
        # Initialization 
        if not self.xavier_init: 
            self.W = torch.randn(self.visible_units,self.hidden_units) * 0.01 #weights 
        else: 
            self.xavier_value = torch.sqrt(torch.FloatTensor([1.0 / (self.visible_units + self.hidden_units)])) 
            self.W = -self.xavier_value + torch.rand(self.visible_units, self.hidden_units) * (2 * self.xavier_value) 
        self.h_bias = torch.zeros(self.hidden_units) #hidden layer bias 
        self.v_bias = torch.zeros(self.visible_units) #visible layer bias 
 
 
 
    def to_hidden(self ,X): 
        ''' 
        Converts the data in visible layer to hidden layer 
        also does sampling 
        X here is the visible probabilities 
        :param X: torch tensor shape = (n_samples , n_features) 
        :return -  X_prob - new hidden layer (probabilities) 
                    sample_X_prob - Gibbs sampling of hidden (1 or 0) based 
                                on the value 
        ''' 
        X_prob = torch.matmul(X,self.W) 
        X_prob = torch.add(X_prob, self.h_bias)#W.x + c 
        X_prob  = torch.sigmoid(X_prob) 
 
 
        sample_X_prob = self.sampling(X_prob) 
 
 
        return X_prob,sample_X_prob 
 
 
    def to_visible(self,X): 
        ''' 
        reconstructs data from hidden layer 
        also does sampling 
        X here is the probabilities in the hidden layer 
        :returns - X_prob - the new reconstructed layers(probabilities) 
                    sample_X_prob - sample of new layer(Gibbs Sampling) 
        ''' 
        # computing hidden activations and then converting into probabilities 
        X_prob = torch.matmul(X ,self.W.transpose( 0 , 1) ) 
        X_prob = torch.add(X_prob , self.v_bias) 
        X_prob = torch.sigmoid(X_prob) 
 
 
        sample_X_prob = self.sampling(X_prob) 
 
 
        return X_prob,sample_X_prob 
 
 
    def sampling(self,prob): 
        ''' 
        Bernoulli sampling done based on probabilities s 
        ''' 
        s = torch.distributions.Bernoulli(prob).sample() 
        return s 
 
 
    def reconstruction_error(self , data): 
        ''' 
        Computes the reconstruction error for the data 
        handled by pytorch by loss functions 
        ''' 
        return self.contrastive_divergence(data, False) 
 
 
    def reconstruct(self , X,n_gibbs): 
        ''' 
        This will reconstruct the sample with k steps of gibbs Sampling 
        ''' 
        v = X 
        for i in range(n_gibbs): 
            prob_h_,h = self.to_hidden(v) 
            prob_v_,v = self.to_visible(prob_h_) 
        return prob_v_,v 
 
 
 
    def contrastive_divergence(self, input_data ,training = True, 
                                n_gibbs_sampling_steps=1,lr = 0.001): 
        # positive phase 
 
 
        positive_hidden_probabilities,positive_hidden_act  = self.to_hidden(input_data) 
 
 
        # calculating W via positive side 
        positive_associations = torch.matmul(input_data.t() , positive_hidden_act) 
 
 
 
 
        # negetive phase 
        hidden_activations = positive_hidden_act 
        for i in range(n_gibbs_sampling_steps): 
            visible_probabilities , _ = self.to_visible(hidden_activations) 
            hidden_probabilities,hidden_activations = self.to_hidden(visible_probabilities) 
 
 
        negative_visible_probabilities = visible_probabilities 
        negative_hidden_probabilities = hidden_probabilities 
 
 
        # calculating W via negative side 
        negative_associations = torch.matmul(negative_visible_probabilities.t() , negative_hidden_probabilities) 
 
 
 
        # Update parameters 
        if(training): 
 
 
            batch_size = self.batch_size 
 
 
            g = (positive_associations - negative_associations) 
            grad_update = g / batch_size 
            v_bias_update = torch.sum(input_data - negative_visible_probabilities,dim=0)/batch_size 
            h_bias_update = torch.sum(positive_hidden_probabilities - negative_hidden_probabilities,dim=0)/batch_size 
 
 
            self.W += lr * grad_update 
            self.v_bias += lr * v_bias_update 
            self.h_bias += lr * h_bias_update 
 
 
 
        # Compute reconstruction error 
        error = torch.mean(torch.sum((input_data - negative_visible_probabilities)**2 , dim = 0)) 
 
 
        return error,torch.sum(torch.abs(grad_update)) 
 
 
 
    def forward(self,input_data): 
        'data->hidden' 
        return  self.to_hidden(input_data) 
    def step(self,input_data,epoch,num_epochs): 
        ''' 
            Includes the foward prop plus the gradient descent 
            Use this for training 
        ''' 
        if self.increase_to_cd_k: 
            n_gibbs_sampling_steps = int(math.ceil((epoch/num_epochs) * self.k)) 
        else: 
            n_gibbs_sampling_steps = self.k 
 
 
        if self.learning_rate_decay: 
            lr = self.learning_rate / epoch 
        else: 
            lr = self.learning_rate 
 
 
        return self.contrastive_divergence(input_data , True,n_gibbs_sampling_steps,lr); 
 
 
 
    def train(self,train_dataloader , num_epochs = 50,batch_size=16): 
 
 
        self.batch_size = batch_size 
        if(isinstance(train_dataloader ,torch.utils.data.DataLoader)): 
            train_loader = train_dataloader 
        else: 
            train_loader = torch.utils.data.DataLoader(train_dataloader, batch_size=batch_size) 
 
 
 
        for epoch in range(1 , num_epochs+1): 
            epoch_err = 0.0 
            n_batches = int(len(train_loader)) 
            # print(n_batches) 
 
 
            cost_ = torch.FloatTensor(n_batches , 1) 
            grad_ = torch.FloatTensor(n_batches , 1) 
 
 
            for i,(batch,_) in tqdm(enumerate(train_loader),ascii=True, 
                                desc="RBM fitting", file=sys.stdout): 
 
 
                batch = batch.view(len(batch) , self.visible_units) 
                 
                if(self.use_gpu): 
                    batch = batch.cuda() 
                cost_[i-1],grad_[i-1] = self.step(batch,epoch,num_epochs) 
 
 
 
            print("Epoch:{} ,avg_cost = {} ,std_cost = {} ,avg_grad = {} ,std_grad = {}".format(epoch,\ 
                                                            torch.mean(cost_),\ 
                                                            torch.std(cost_),\ 
                                                            torch.mean(grad_),\ 
                                                            torch.std(grad_))) 
 
 
        return 
 
 
 
 
DBM_main.py 
 
# Importing the libraries 
from DBN import DBN 
import torch  
import torchvision 
from torchvision import datasets,transforms 
from torch.utils.data import Dataset,DataLoader 
from torchvision.transforms import ToTensor 
import matplotlib 
import matplotlib.pyplot as plt 
 
 
import math 
import numpy as np 
 
 
from codecarbon import EmissionsTracker 
 
 
from codecarbon.output import GoogleCloudLoggerOutput, LoggerOutput 
 
 
import google.cloud.logging 
 
 
import time 
 
 
 
start = time .time () 
 
 
# Create a Cloud Logging client (specify project name if needed, otherwise Google SDK default project name is used) 
client = google.cloud.logging.Client(project='My Project 61992') 
 
 
my_logger = GoogleCloudLoggerOutput(client.logger('DBM_carbon_log')) 
# Create a Code Carbon GoogleCloudLoggerOutput with the Cloud Logging logger, with the logging level to be used for emissions data messages 
tracker = EmissionsTracker(save_to_logger=True, logging_logger=my_logger) 
tracker.start() 
 
 
 
#Loading MNIST dataset 
train_data = datasets.MNIST( 
    root=".", 
    train=True, 
    transform=ToTensor(), 
    download=True, 
) 
test_data = datasets.MNIST(root=".", train=False, transform=ToTensor()) 
 
 
#Lets us visualize a number from the data set 
idx = 5 
img = test_data.train_data[idx] 
print("The number shown is the number: {}".format(test_data.train_labels[idx]) ) 
plt.imshow(img , cmap = 'gray') 
plt.show() 
 
 
# I have have set these hyper parameters although you can experiment with them to find better hyperparameters. 
dbn_mnist = DBN(visible_units=28*28 , 
                hidden_units=[23*23 ,18*18] , 
                k = 5, 
                learning_rate = 0.01, 
                learning_rate_decay = True, 
                xavier_init = True, 
                increase_to_cd_k = False, 
                use_gpu = False) 
num_epochs = 1 
batch_size = 10 
 
 
dbn_mnist.train_static(test_data.train_data,test_data.train_labels,num_epochs , batch_size) 
 
 
learned_weights = dbn_mnist.rbm_layers[0].W.transpose(0,1).numpy() 
plt.show() 
fig = plt.figure(3, figsize=(10,10)) 
for i in range(25):  
    sub = fig.add_subplot(5, 5, i+1) 
    sub.imshow(learned_weights[i,:].reshape((28,28)), cmap=plt.cm.gray) 
plt.show() 
 
 
learned_weights = dbn_mnist.rbm_layers[1].W.transpose(0,1).numpy() 
plt.show() 
fig = plt.figure(3, figsize=(10,10)) 
for i in range(25):  
    sub = fig.add_subplot(5, 5, i+1) 
    sub.imshow(learned_weights[i,:].reshape((23,23)), cmap=plt.cm.gray) 
plt.show() 
 
 
number = 5 #A number between 0 and 10. 
 
 
particular_mnist = [] 
 
 
limit = test_data.train_data.shape[0] 
# limit = 60000 
for i in range(limit): 
    if(test_data.train_labels[i] == number): 
        particular_mnist.append(test_data.train_data[i].numpy()) 
# particular_mnist = np.array(particular_mnist) 
len(particular_mnist) 
# mnist_data.train_data 
5421 
train_data = torch.stack([torch.Tensor(i) for i in particular_mnist]) 
train_label = torch.stack([torch.Tensor(number) for i in range(len(particular_mnist))]) 
dbn_mnist.train_static(train_data,train_label,20 , batch_size) 
 
 
idx = 3 
img = test_data.train_data[idx] 
reconstructed_img = img.view(1,-1).type(torch.FloatTensor) 
 
 
_,reconstructed_img= dbn_mnist.reconstruct(reconstructed_img) 
 
 
reconstructed_img = reconstructed_img.view((28,28)) 
print("The original number: {}".format(test_data.train_labels[idx])) 
plt.imshow(img , cmap = 'gray') 
plt.show() 
print("The reconstructed image") 
plt.imshow(reconstructed_img , cmap = 'gray') 
plt.show() 
 
 
 
 
tracker.flush() 
tracker.stop() 
 
 
end = time .time ()  
print( end - start) 
 
 
Appendix 9 
Gated Recurrent Unit 
 
import matplotlib.pyplot as plt 
import numpy as np 
import torch 
import torch.nn as nn 
import torchvision.transforms as transforms 
import torchvision.datasets as dsets 
from torch.autograd import Variable 
from torch.nn import Parameter 
from torch import Tensor 
import torch.nn.functional as F 
 
 
import math 
 
 
from codecarbon import EmissionsTracker 
 
 
from codecarbon.output import GoogleCloudLoggerOutput, LoggerOutput 
 
 
import google.cloud.logging 
 
 
import time 
 
 
start = time .time () 
 
 try:
# Create a Cloud Logging client (specify project name if needed, otherwise Google SDK default project name is used) 
client = google.cloud.logging.Client(project='My Project 61992')
except:
	print(“not on GCP”) 
 
 
my_logger = GoogleCloudLoggerOutput(client.logger('GRU_carbon_log')) 
 
 
tracker = EmissionsTracker(save_to_logger=True, logging_logger=my_logger) 
tracker.start() 
 
 
loss_gru = np.loadtxt("loss_gru.txt") 
loss_lstm = np.loadtxt("loss_lstm.txt") 
loss_gru = loss_gru.astype(np.float64) 
loss_lstm = loss_lstm.astype(np.float64) 
two_loss = np.vstack((loss_gru, loss_lstm)) 
 
 
plt.xlabel("Iteration") 
plt.ylabel("Loss (CrossEntropyLoss)") 
plt.title("MNIST Learning curve for LSTM and GRU") 
plt.plot(two_loss.T[:,0],label="GRU") 
plt.plot(two_loss.T[:,1], label="LSTM") 
plt.legend() 
 
 
 
cuda = True if torch.cuda.is_available() else False 
     
Tensor = torch.cuda.FloatTensor if cuda else torch.FloatTensor     
 
 
torch.manual_seed(125) 
if torch.cuda.is_available(): 
    torch.cuda.manual_seed_all(125) 
 
 
train_dataset = dsets.MNIST(root='./data',  
                            train=True,  
                            transform=transforms.ToTensor(), 
                            download=True) 
  
test_dataset = dsets.MNIST(root='./data',  
                           train=False,  
                           transform=transforms.ToTensor()) 
  
batch_size = 100 
n_iters = 6000 
num_epochs = n_iters / (len(train_dataset) / batch_size) 
num_epochs = int(num_epochs) 
train_loader = torch.utils.data.DataLoader(dataset=train_dataset,  
                                           batch_size=batch_size,  
                                           shuffle=True) 
  
test_loader = torch.utils.data.DataLoader(dataset=test_dataset,  
                                          batch_size=batch_size,  
                                          shuffle=False) 
 
 
class GRUCell(nn.Module): 
 
 
    """ 
    An implementation of GRUCell. 
 
 
    """ 
 
 
    def __init__(self, input_size, hidden_size, bias=True): 
        super(GRUCell, self).__init__() 
        self.input_size = input_size 
        self.hidden_size = hidden_size 
        self.bias = bias 
        self.x2h = nn.Linear(input_size, 3 * hidden_size, bias=bias) 
        self.h2h = nn.Linear(hidden_size, 3 * hidden_size, bias=bias) 
        self.reset_parameters() 
 
 
 
 
    def reset_parameters(self): 
        std = 1.0 / math.sqrt(self.hidden_size) 
        for w in self.parameters(): 
            w.data.uniform_(-std, std) 
     
    def forward(self, x, hidden): 
         
        x = x.view(-1, x.size(1)) 
         
        gate_x = self.x2h(x)  
        gate_h = self.h2h(hidden) 
         
        gate_x = gate_x.squeeze() 
        gate_h = gate_h.squeeze() 
         
        i_r, i_i, i_n = gate_x.chunk(3, 1) 
        h_r, h_i, h_n = gate_h.chunk(3, 1) 
         
         
        resetgate = torch.sigmoid(i_r + h_r) 
        inputgate = torch.sigmoid(i_i + h_i) 
        newgate = torch.tanh(i_n + (resetgate * h_n)) 
         
        hy = newgate + inputgate * (hidden - newgate) 
         
         
        return hy 
 
 
class GRUModel(nn.Module): 
    def __init__(self, input_dim, hidden_dim, layer_dim, output_dim, bias=True): 
        super(GRUModel, self).__init__() 
        # Hidden dimensions 
        self.hidden_dim = hidden_dim 
          
        # Number of hidden layers 
        self.layer_dim = layer_dim 
          
        
        self.gru_cell = GRUCell(input_dim, hidden_dim, layer_dim) 
         
         
        self.fc = nn.Linear(hidden_dim, output_dim) 
      
     
     
    def forward(self, x): 
         
        # Initialize hidden state with zeros 
        ####################### 
        #  USE GPU FOR MODEL  # 
        ####################### 
        #print(x.shape,"x.shape")100, 28, 28 
        if torch.cuda.is_available(): 
            h0 = Variable(torch.zeros(self.layer_dim, x.size(0), self.hidden_dim).cuda()) 
        else: 
            h0 = Variable(torch.zeros(self.layer_dim, x.size(0), self.hidden_dim)) 
          
        
        outs = [] 
         
        hn = h0[0,:,:] 
         
        for seq in range(x.size(1)): 
            hn = self.gru_cell(x[:,seq,:], hn)  
            outs.append(hn) 
             
 
 
        out = outs[-1].squeeze() 
         
        out = self.fc(out)  
        # out.size() --> 100, 10 
        return out 
 
 
class LSTMModel(nn.Module): 
    def __init__(self, input_dim, hidden_dim, layer_dim, output_dim, bias=True): 
        super(LSTMModel, self).__init__() 
        # Hidden dimensions 
        self.hidden_dim = hidden_dim 
          
        # Number of hidden layers 
        self.layer_dim = layer_dim 
                
        self.lstm = LSTMCell(input_dim, hidden_dim, layer_dim)   
         
        self.fc = nn.Linear(hidden_dim, output_dim) 
      
     
     
    def forward(self, x): 
         
        # Initialize hidden state with zeros 
        ####################### 
        #  USE GPU FOR MODEL  # 
        ####################### 
        #print(x.shape,"x.shape")100, 28, 28 
        if torch.cuda.is_available(): 
            h0 = Variable(torch.zeros(self.layer_dim, x.size(0), self.hidden_dim).cuda()) 
        else: 
            h0 = Variable(torch.zeros(self.layer_dim, x.size(0), self.hidden_dim)) 
 
 
        # Initialize cell state 
        if torch.cuda.is_available(): 
            c0 = Variable(torch.zeros(self.layer_dim, x.size(0), self.hidden_dim).cuda()) 
        else: 
            c0 = Variable(torch.zeros(self.layer_dim, x.size(0), hidden_dim)) 
 
 
                     
        
        outs = [] 
         
        cn = c0[0,:,:] 
        hn = h0[0,:,:] 
 
 
        for seq in range(x.size(1)): 
            hn, cn = self.lstm(x[:,seq,:], (hn,cn))  
            outs.append(hn) 
             
     
 
 
        out = outs[-1].squeeze() 
         
        out = self.fc(out)  
        # out.size() --> 100, 10 
        return out 
 
 
input_dim = 28 
hidden_dim = 128 
layer_dim = 1  # ONLY CHANGE IS HERE FROM ONE LAYER TO TWO LAYER 
output_dim = 10 
  
# model = LSTMModel(input_dim, hidden_dim, layer_dim, output_dim) 
model = GRUModel(input_dim, hidden_dim, layer_dim, output_dim) 
 
 
####################### 
#  USE GPU FOR MODEL  # 
####################### 
  
if torch.cuda.is_available(): 
    model.cuda() 
      
''' 
STEP 5: INSTANTIATE LOSS CLASS 
''' 
criterion = nn.CrossEntropyLoss() 
  
''' 
STEP 6: INSTANTIATE OPTIMIZER CLASS 
''' 
learning_rate = 0.1 
  
optimizer = torch.optim.SGD(model.parameters(), lr=learning_rate)   
 
 
# Number of steps to unroll 
seq_dim = 28  
 
 
loss_list = [] 
iter = 0 
for epoch in range(num_epochs): 
    for i, (images, labels) in enumerate(train_loader): 
        # Load images as Variable 
        ####################### 
        #  USE GPU FOR MODEL  # 
        ####################### 
           
        if torch.cuda.is_available(): 
            images = Variable(images.view(-1, seq_dim, input_dim).cuda()) 
            labels = Variable(labels.cuda()) 
        else: 
            images = Variable(images.view(-1, seq_dim, input_dim)) 
            labels = Variable(labels) 
           
        # Clear gradients w.r.t. parameters 
        optimizer.zero_grad() 
          
        # Forward pass to get output/logits 
        # outputs.size() --> 100, 10 
        outputs = model(images) 
 
 
        # Calculate Loss: softmax --> cross entropy loss 
        loss = criterion(outputs, labels) 
 
 
        if torch.cuda.is_available(): 
            loss.cuda() 
 
 
        # Getting gradients w.r.t. parameters 
        loss.backward() 
 
 
        # Updating parameters 
        optimizer.step() 
         
        loss_list.append(loss.item()) 
        iter += 1 
          
        if iter % 500 == 0: 
            # Calculate Accuracy          
            correct = 0 
            total = 0 
            # Iterate through test dataset 
            for images, labels in test_loader: 
                ####################### 
                #  USE GPU FOR MODEL  # 
                ####################### 
                if torch.cuda.is_available(): 
                    images = Variable(images.view(-1, seq_dim, input_dim).cuda()) 
                else: 
                    images = Variable(images.view(-1 , seq_dim, input_dim)) 
                 
                # Forward pass only to get logits/output 
                outputs = model(images) 
                 
                # Get predictions from the maximum value 
                _, predicted = torch.max(outputs.data, 1) 
                  
                # Total number of labels 
                total += labels.size(0) 
                  
                # Total correct predictions 
                ####################### 
                #  USE GPU FOR MODEL  # 
                ####################### 
                if torch.cuda.is_available(): 
                    correct += (predicted.cpu() == labels.cpu()).sum() 
                else: 
                    correct += (predicted == labels).sum() 
              
            accuracy = 100 * correct / total 
              
            # Print Loss 
            print('Iteration: {}. Loss: {}. Accuracy: {}'.format(iter, loss.item(), accuracy)) 
 
 
end = time .time ()  
 
 
print ( end - start) 
