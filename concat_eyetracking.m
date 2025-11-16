% concat eye tracking data
nr_path  = 'G:\我的云端硬盘\Zuco2\task1 - NR\Raw data';
tsr_path = 'G:\我的云端硬盘\Zuco2\task2 - TSR\Raw data';
out_path = 'D:\Zuco\ET_concat_data';

subjects = {'YAC','YAG','YAK','YDG','YDR','YFR','YFS','YHS','YIS',...
            'YLS','YMD','YMS','YRH','YRK','YRP','YSD','YSL','YTL'};

drop_list = { ...
  'YAC_NR5_EEG.mat','YAC_NR6_EEG.mat','YAC_TSR4_EEG.mat','YAC_TSR5_EEG.mat',...
  'YDG_NR5_EEG.mat','YDG_TSR5_EEG.mat','YDG_TSR6_EEG.mat','YFR_TSR2_EEG.mat',...
  'YLS_NR1_EEG.mat','YLS_NR2_EEG.mat','YLS_TSR1_EEG.mat',...
  'YMS_NR1_EEG.mat','YMS_NR2_EEG.mat','YMS_NR3_EEG.mat','YMS_NR4_EEG.mat',...
  'YMS_NR6_EEG.mat','YMS_NR7_EEG.mat','YMS_TSR1_EEG.mat','YMS_TSR3_EEG.mat','YMS_TSR5_EEG.mat',...
  'YRH_NR1_EEG.mat','YRH_NR2_EEG.mat','YRH_TSR1_EEG.mat','YRH_TSR4_EEG.mat'};

for s = 1:length(subjects)
    subj = subjects{s};
    ET_all = {};   

    % NR blocks
    for b = 1:7
        if ismember(sprintf('%s_NR%d_EEG.mat', subj, b), drop_list), continue; end
        f = fullfile(nr_path, subj, sprintf('%s_NR%d_ET.mat', subj, b));
        if exist(f,'file')
            tmp = load(f); 
            ET_all{end+1} = tmp;   
        end
    end

    % TSR blocks
    for b = 1:7
        if ismember(sprintf('%s_TSR%d_EEG.mat', subj, b), drop_list), continue; end
        f = fullfile(tsr_path, subj, sprintf('%s_TSR%d_ET.mat', subj, b));
        if exist(f,'file')
            tmp = load(f);
            ET_all{end+1} = tmp;
        end
    end

    save(fullfile(out_path, sprintf('%s_concat_ET.mat', subj)), 'ET_all');
end
