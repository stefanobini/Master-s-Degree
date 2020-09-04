for i = 1:10
    message=strcat('Pre-process network ', int2str(i));
    disp(message);
    path=strcat('../PPMI/drug_net_', int2str(i), '.mat');
    PPMI=load(path);
    Net=full(PPMI.Net);
    % dir_matrix=symmetric_networks(Net);
    dir_matrix=regulatory_networks(Net);
    path=strcat('../dir_matrices/drug_dir_net_', int2str(i), '.mat');
    save(path, 'dir_matrix');
end