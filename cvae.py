import argparse

import torch
from torch import nn
from torch import optim
from torch.nn import functional
from torch.utils.data import DataLoader
from torchsummary import summary
import numpy as np
from sklearn.model_selection import KFold
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score
from sklearn.metrics import average_precision_score
from torch.autograd import Variable
import matplotlib.pyplot as plt


def regularization(mu, logvar):
    return -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())


def Guassian_loss(recon_x, x):
    weights = x * args.alpha + (1 - x)
    loss = x - recon_x
    loss = torch.sum(weights * loss * loss)
    return loss


def BCE_loss(recon_x, x):
    eps = 1e-8
    loss = -torch.sum(args.alpha * torch.log(recon_x + eps) * x + torch.log(1 - recon_x + eps) * (1 - x))
    return loss


def train(epoch):
    model.train()
    loss_value = 0
    for batch_idx, data in enumerate(train_loader):

        data = data.to(args.device)
        data = Variable(data)
        optimizer.zero_grad()
        recon_batch, mu, logvar = model(data)

        loss = loss_function(recon_batch, data) + regularization(mu, logvar) * args.beta
        loss.backward()
        loss_value += loss.item()
        optimizer.step()
        if args.log != 0 and batch_idx % args.log == 0:
            print('Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}'.format(
                epoch, batch_idx * len(data), len(train_loader.dataset),
                       100. * batch_idx / len(train_loader),
                       loss.item() / len(data)))

    print('====> Epoch: {} Average loss: {:.4f}'.format(
        epoch, loss_value / len(train_loader.dataset)))
    return loss_value / len(train_loader.dataset)


# Implementation of Variaitonal Autoencoder
class VAE(nn.Module):
    # Define the initialization function，which defines the basic structure of the neural network
    def __init__(self, args):
        super(VAE, self).__init__()
        self.l = len(args.layer)
        self.L = args.L
        self.device = args.device
        self.inet = nn.ModuleList()
        darray = [args.d] + args.layer
        for i in range(self.l - 1):
            self.inet.append(nn.Linear(darray[i], darray[i + 1]))
        self.mu = nn.Linear(darray[self.l - 1], darray[self.l])
        self.sigma = nn.Linear(darray[self.l - 1], darray[self.l])
        self.gnet = nn.ModuleList()
        for i in range(self.l):
            self.gnet.append(nn.Linear(darray[self.l - i], darray[self.l - i - 1]))

    def encode(self, x):
        h = x
        for i in range(self.l - 1):
            h = functional.relu(self.inet[i](h))
            # h = functional.relu(functional.dropout(self.inet[i](h), p=0.5, training=True))
        return self.mu(h), self.sigma(h)

    def decode(self, z):
        h = z
        for i in range(self.l - 1):
            h = functional.relu(self.gnet[i](h))
            # h = functional.relu(functional.dropout(self.gnet[i](h), p=0.5, training=True))
        return functional.sigmoid(self.gnet[self.l - 1](h))

    def reparameterize(self, mu, logvar):
        if self.training:
            std = torch.exp(0.5 * logvar)
            eps = torch.randn([self.L] + list(std.shape)).to(self.device)
            return eps.mul(std).add_(mu)
        else:
            return mu

    # Define the forward propagation function for the neural network.
    # Once defined, the backward propagation function will be autogeneration（autograd）
    def forward(self, x):
        mu, logvar = self.encode(x)
        z = self.reparameterize(mu, logvar)
        return self.decode(z), mu, logvar


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Variational Auto Encoder')
    parser.add_argument('--batch', type=int, default=100, help='input batch size for training (default: 100)')
    parser.add_argument('-m', '--maxiter', type=int, default=10, help='number of epochs to train (default: 10)')
    parser.add_argument('--gpu', action='store_true', default=False, help='enables CUDA training')
    parser.add_argument('--seed', type=int, default=1, help='random seed (default: 1)')
    parser.add_argument('--log', type=int, default=1, metavar='N',
                        help='how many batches to wait before logging training status')
    parser.add_argument('--dir', help='dataset directory', default='/Users/deepDR/dataset')
    parser.add_argument('--layer', nargs='+', help='number of neurals in each layer', type=int, default=[20])
    parser.add_argument('-L', type=int, default=1, help='number of samples')
    parser.add_argument('-N', help='number of recommended items', type=int, default=20)
    parser.add_argument('--learn_rate', help='learning rate', type=float, default=0.001)
    parser.add_argument('-a', '--alpha', help='parameter alpha', type=float, default=1)
    parser.add_argument('-b', '--beta', help='parameter beta', type=float, default=1)
    parser.add_argument('--rating', help='feed input as rating', action='store_true')
    parser.add_argument('--save', help='save model', action='store_true')
    parser.add_argument('--load', help='load model, 1 for fvae and 2 for cvae', type=int, default=0)

    args = parser.parse_args()
    torch.manual_seed(args.seed)
    # whether to ran with cuda
    args.device = torch.device("cuda" if args.gpu and torch.cuda.is_available() else "cpu")

    print('dataset directory: ' + args.dir)
    directory = args.dir

    path = '{}/drugDisease.txt'.format(directory)   # 2-D matrix of drug-disease network
    print('train data path: ' + path)
    R = np.loadtxt(path)                            # 2-D matrix of disease-drug network
    Rtensor = R.transpose()
    if args.rating:  # feed in with rating
        whole_positive_index = []   # It is np array containing the pair disease-drug index that have some interactions.
                                    # Example {[idx_disease567, idx_drug22], [idx_disease988, idx_drug5000], ...}
        whole_negative_index = []   # It is np array containing the pair disease-drug index that have no interactions.
        for i in range(np.shape(Rtensor)[0]):
            for j in range(np.shape(Rtensor)[1]):
                if int(Rtensor[i][j]) == 1:         # there is interaction between disease 'i' and drug 'j'
                    whole_positive_index.append([i, j])
                elif int(Rtensor[i][j]) == 0:       # there is no interaction between disease 'i' and drug 'j'
                    whole_negative_index.append([i, j])
        negative_sample_index = np.random.choice(np.arange(len(whole_negative_index)),
                                                 size=1 * len(whole_positive_index), replace=False)     # mix the index without replacement
        # whole_negative_index=np.array(whole_negative_index)
        data_set = np.zeros((len(negative_sample_index) + len(whole_positive_index), 3), dtype=int)     # build empty integer dataset with shape = (n_disease * n_drugs * 3)
        count = 0
        for i in whole_positive_index:
            data_set[count][0] = i[0]   # assign the disease from the first index of whole_positive_index array
            data_set[count][1] = i[1]   # assign the drug from the second index of whole_positive_index array
            data_set[count][2] = 1      # set interaction between disease and drug
            count += 1
        for i in negative_sample_index:
            data_set[count][0] = whole_negative_index[i][0]     # assign the disease from the first index of whole_negative_index array
            data_set[count][1] = whole_negative_index[i][1]     # assign the drug from the second index of whole_negative array
            data_set[count][2] = 0                              # set no interaction between disease and drug
            count += 1
        test_auc_fold = []
        test_aupr_fold = []
        rs = np.random.randint(0, 1000, 1)[0]
        # kf = StratifiedKFold(data_set[:, 2], n_folds=5, shuffle=True, random_state=rs)    # this definition is deprecated
        kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=rs)     # build object to make 'k fold validation' on the dataset

        for train_index, test_index in kf.split(data_set[:, :1], data_set[:, 2]):   # apply 'k fold validation'
            DTItrain, DTItest = data_set[train_index], data_set[test_index]         # generate a fold with 1 of 5 parts of dataset
            Xtrain = np.zeros((np.shape(Rtensor)[0], np.shape(Rtensor)[1]))         # build a np array with same shape of disease-drug matrix as training set, it will contain the disease-drug interaction
            for ele in DTItrain:
                Xtrain[ele[0], ele[1]] = ele[2]     # fill Xtrain with the interaction values
            Rtensor = torch.from_numpy(Xtrain.astype('float32')).to(args.device)
            args.d = Rtensor.shape[1]   # number of drugs
            train_loader = DataLoader(Rtensor, args.batch, shuffle=True)    # build DataLoader object in order use an iterator to feed the training
            loss_function = BCE_loss    # set loss function

            model = VAE(args).to(args.device)   # set device on that the model will be trained
            print(model)
            if args.load > 0:
                name = 'cvae' if args.load == 2 else 'fvae'
                path = 'test_models/' + name
                for l in args.layer:
                    path += '_' + str(l)
                print('load model from path: ' + path)
                model.load_state_dict(torch.load(path))     # load model

            optimizer = optim.Adam(model.parameters(), lr=args.learn_rate)  # set optimizer

            loss_list = []
            for epoch in range(1, args.maxiter + 1):    # run training on 'args.maxiter' epochs
                loss = train(epoch)
                loss_list.append(loss)

            model.eval()    # evaluate the trained model
            score, _, _ = model(Rtensor)
            print(score.cpu().detach().numpy().shape)
            Zscore = score.cpu().detach().numpy()

            pred_list = []
            ground_truth = []
            for ele in DTItrain:    # calculate reached performance on the train set (auc, aupr) by difference between groundtruth and predicted values
                pred_list.append(Zscore[ele[0], ele[1]])
                ground_truth.append(ele[2])
            train_auc = roc_auc_score(ground_truth, pred_list)
            train_aupr = average_precision_score(ground_truth, pred_list)
            print('train auc aupr,', train_auc, train_aupr)
            pred_list = []
            ground_truth = []
            for ele in DTItest:     # calculate reached performance on the test set (auc, aupr) by difference between groundtruth and predicted values
                pred_list.append(Zscore[ele[0], ele[1]])
                ground_truth.append(ele[2])
            test_auc = roc_auc_score(ground_truth, pred_list)
            test_aupr = average_precision_score(ground_truth, pred_list)
            print('test auc aupr', test_auc, test_aupr)
            test_auc_fold.append(test_auc)
            test_aupr_fold.append(test_aupr)
            # model.train()
        avg_auc = np.mean(test_auc_fold)    # calculate average performance on the 5 fold
        avg_pr = np.mean(test_aupr_fold)
        print('mean auc aupr', avg_auc, avg_pr)

    else:  # feed in with side information
        path = 'drugmdaFeatures.txt'
        print('feature data path: ' + path)
        fea = np.loadtxt(path)
        X = fea.transpose()
        X[X > 0] = 1
        args.d = X.shape[1]
        # X = normalize(X, axis=1)
        X = torch.from_numpy(X.astype('float32')).to(args.device)
        train_loader = DataLoader(X, args.batch, shuffle=True)
        loss_function = Guassian_loss   # this training take as input only the embeddings extracted by MDA and train
                                        # the model perform a sort of comparison with a Gaussian distribution

        model = VAE(args).to(args.device)
        if args.load > 0:
            name = 'cvae' if args.load == 2 else 'fvae'
            path = 'test_models/' + name
            for l in args.layer:
                path += '_' + str(l)
            print('load model from path: ' + path)
            model.load_state_dict(torch.load(path))

        optimizer = optim.Adam(model.parameters(), lr=args.learn_rate)

        for epoch in range(1, args.maxiter + 1):
            train(epoch)

    if args.save:
        name = 'cvae' if args.rating else 'fvae'
        path = 'test_models/' + name
        for l in args.layer:
            path += '_' + str(l)
        model.cpu()
        torch.save(model.state_dict(), path)

        foutput = path + '_summary.txt'
        with open(foutput, 'w') as fout:
            output_text = "Model's state_dict:\n"
            for param_tensor in model.state_dict():
                output_text += '{}\t{}\n'.format(param_tensor, model.state_dict()[param_tensor].size())
            fout.write(output_text)