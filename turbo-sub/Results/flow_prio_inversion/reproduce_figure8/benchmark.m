clc

for loadi = [1:1:8]
%     clear all

    %%%d%
    % These parameters need to be input based on the ns2 traffic pattern
    %%%%
    num_ports = 144;
    ['~/Workspace/Turbo/Results/pFabric_original/reproduce_figure8/Dataset/flow_0.', int2str(loadi), 'Load.tr']
    fp = fopen(['~/Workspace/Turbo/Results/pFabric_original/reproduce_figure8/Dataset/flow_0.', int2str(loadi), 'Load.tr']);
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %A = fscanf(fp,'stats: start %f grp %d %d pkts %f\n', [4,inf]);
    A = fscanf(fp, '%f %f %f %f %f %f %f\n', [7, inf]);
    A = A';
    A = sortrows(A, 1);
    fclose(fp);

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    servers_per_TOR = 16;
    %link_speed = 0.99 * 10e9/8/1500; % in packets/microseconds
	link_speed = 10e9/8/1500;
    num_flows = length(A(:,1));
    flow_start_time = A(:,1); % sorted list of flow start time
    flow_source = fix(1 + A(:,6));
    flow_dest = fix(1 + A(:,7));
    flow_size = A(:,3);
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    total_bps = sum(flow_size) * 1500 * 8 / (flow_start_time(end) - flow_start_time(1));
    load = total_bps / num_ports / (1e10)
    
    thresh = 1e-8;

    VOQ = {};
    for i = 1:num_ports
     for j = 1:num_ports
            VOQ{i,j} = [];
     end
    end

    fct = -1 * ones(num_flows,1);
    num_flows_complete = 0;
    VOQs_in_progress = [];
    next_transition = flow_start_time(1);
    next_flow_index = 1;
    cur_time = next_transition;
    while (num_flows_complete < num_flows) 
        % make progress until next_transition
        delta = next_transition - cur_time;
        cur_time = next_transition;
        

        % drain VOQs_in_progress
        if ~isempty(VOQs_in_progress)
            for k = 1:length(VOQs_in_progress(:,1)) 
                q_i = VOQs_in_progress(k,1);
                q_o = VOQs_in_progress(k,2);
                flow_rem = VOQ{q_i,q_o}(1,2) - delta * link_speed;
                VOQ{q_i,q_o}(1,2) = flow_rem;
                if (flow_rem < thresh) % the flow is done 
                    index = VOQ{q_i,q_o}(1,1);
                    fct(index) = cur_time - flow_start_time(index);
                    if fct(index) < 0
                      cur_time 
                      flow_start_time(index)
                      flow_size(index)
                    end
                    VOQ{q_i,q_o}(1,:) = []; % remove flow from VOQ
                    num_flows_complete = num_flows_complete + 1;
                    if (mod(num_flows_complete, 1000) == 0) 
                        disp([num2str(cur_time),': flow ', num2str(index), ' is done'])
                    end                
                end      
            end
        end

        % insert new flow if its time
        if (next_flow_index <= num_flows && cur_time > flow_start_time(next_flow_index) - thresh) 
            src = flow_source(next_flow_index);
            dst = flow_dest(next_flow_index);
            size = flow_size(next_flow_index);
            VOQ{src,dst} = [VOQ{src,dst}; next_flow_index, size];
            %if (next_flow_index == 500) 
            %    [src, dst, size]
            %    cur_time
            %    VOQ{src,dst}
            %end
            % sort VOQ increasing in size
            thisVOQ = VOQ{src,dst};
            [temp,I] = sort(thisVOQ,1);
            temp(:,1) = thisVOQ(I(:,2),1);
            temp(:,2) = thisVOQ(I(:,2),2);
            VOQ{src,dst} = temp;
            %
            %if (next_flow_index == 500)
            %    VOQ{src,dst}
            %end
            
            next_flow_index = next_flow_index + 1;
        end
    
        % schedule VOQs
        VOQ_heads = []; % temporary list will have format (src, dst, size)
        VOQs_in_progress = [];
        free_inputs = ones(1,num_ports);
        free_outputs = ones(1,num_ports);
        for i = 1:num_ports
            for j = 1:num_ports
                if ~isempty(VOQ{i,j})
                    VOQ_heads = [VOQ_heads; i,j,VOQ{i,j}(1,2)];
                end
            end
        end
        next_transition = inf;
        if ~isempty(VOQ_heads)
            %if (next_flow_index > 500)
            %    VOQ_heads
            %    pause
            %end

            [temp,I] = sort(VOQ_heads, 1);
            temp(:,1) = VOQ_heads(I(:,3),1);
            temp(:,2) = VOQ_heads(I(:,3),2);
            temp(:,3) = VOQ_heads(I(:,3),3);
            VOQ_heads = temp;
            for k = 1:length(VOQ_heads(:,1))
                input = VOQ_heads(k,1);
                output = VOQ_heads(k,2);
                size = VOQ_heads(k,3);
                if (free_inputs(input) == 1 && free_outputs(output) == 1)
                    VOQs_in_progress = [VOQs_in_progress; input, output];
                    free_inputs(input) = 0;
                    free_outputs(output) = 0;
                    duration = size / link_speed;
                    if (cur_time + duration < next_transition)
                        next_transition = cur_time + duration;
                    end
                end
            end
        end
    
        if (next_flow_index <= num_flows && flow_start_time(next_flow_index) < next_transition)
            next_transition = flow_start_time(next_flow_index);
        end
    end
  

    fct = fct * 1e6; % change to microseconds
    num_hops = zeros(num_flows,1);
    for i = 1:num_flows
        if (floor(flow_source(i)/servers_per_TOR) == floor(flow_dest(i)/servers_per_TOR)) % same TOR
            num_hops(i) = 2;
        %elseif (floor(flow_source(i)/servers_per_pod) == floor(flow_dest(i)/servers_per_pod)) % same pod
        %    num_hops(i) = 4;
        else
            num_hops(i) = 4;
        end
    end
    correction = (1.632 - 1.2/0.99) + 10 + (num_hops - 1) * 1.632;
    fct = fct + correction;
    %min_fct = flow_size * 1.2 + correction;
    %normalized_fct = fct ./ min_fct;

    %%%%%%%%%%%%%%%%%%%%%%%
    % write results to file
    %%%%%%%%%%%%%%%%%%%%%%%

    fct
    mean(fct)
    
    fp = fopen(['./Dataset/pfabric_result_0.', int2str(loadi), 'Load.txt'],'w');
    for i = 1:length(fct)  
        fprintf(fp, '%g %g 0 %d %d\n', flow_size(i), fct(i)/1e6, flow_source(i)-1, flow_dest(i));    
    end
    %Z = [flow_size, fct, zeros(length(fct),1), flow_source, flow_dest];
    %save([path,'/dctcp-sg1.txt'], Z)

    fclose(fp)
    
end

