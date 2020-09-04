import scipy.io as sio


def is_symmetric(x):
    symmetric = True
    for row in range(len(x)-1):
        for column in range(len(x[row])-1):
            if x[row, column] != x[column, row]:
                return False
    return True


select_nets = [1,2,3,4,5,6,7,8,10]
org = 'drug'
for i in select_nets:
    print("### [%d] Loading network..." % (i))
    N = sio.loadmat(org + '_net_' + str(i) +  '.mat', squeeze_me=True)
    Net = N['Net'].todense()
    print('Network "{}": {}'.format(i, Net.shape))
    print('Network type: ', type(Net))
    print('It is symmetric? ', is_symmetric(Net))
    