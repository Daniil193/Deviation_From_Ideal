import pandas as pd


def get_top_chain_sequences(df, id_col_name, activity_col_name, time_col_name, seq_count_tresh = 100):
    """
    This function define most popular chain sequences in log
    Parameters
    -----------
    seq_count_tresh: (int) - how many chain of sequences return to excel file 
    Returns
    -----------
        top_n_chain_sequences: (DataFrame)
        excel_file
    Example
    -----------
    top_n_chain_sequences = get_top_chain_sequences(my_log, "ids", "events", 100)

    """
    def join_events(vals):
        return "||".join([i for i in vals])

    temp_df = df.sort_values([id_col_name, time_col_name]).copy()

    all_seq = temp_df.groupby(id_col_name).agg({activity_col_name: join_events})

    data = []
    for c, itms in enumerate(dict(all_seq[activity_col_name].value_counts()).items()):
        if c < seq_count_tresh:
            for i, s in enumerate(itms[0].split("||")):
                data.append([c+1, itms[1], i+1, s])
        else:
            break

    df_seq = pd.DataFrame(data, columns=["ChainNumber", 
                                         "ChainFrequency", 
                                         "StepNumberOfChain", 
                                         "EventName"])
#     ends = df_seq.groupby("ChainNumber").last().reset_index()
#     ends["StepNumberOfChain"] = ends["StepNumberOfChain"] + 1
#     ends["EventName"] = "end"

    top_n_chain_sequences = df_seq.sort_values(by=["ChainNumber", "StepNumberOfChain"])#pd.concat([df_seq, ends])
    top_n_chain_sequences.to_excel(f"Top_{seq_count_tresh}_chain_sequences.xlsx", index=False)
    print(f"Result saved to: Top_{seq_count_tresh}_chain_sequences.xlsx")

    return top_n_chain_sequences



def initial_start_event(df, id_col_name, activity_col_name, time_col_name):
    """
    This function initialize start event for the log
    
    Parameters
    ----------
    df:                (pandas DataFrame) - log
    id_col_name:       (str)
    activity_col_name: (str)
    time_col_name:     (str)
    
    Returns
    -----------
    (pandas DataFrame)  - concated origin log with init log
    """
    
    df.sort_values([id_col_name, time_col_name], inplace=True)
    first_df = df.groupby(id_col_name).first().reset_index()
    first_df[activity_col_name] = "start"
    first_df[time_col_name] = first_df[time_col_name] - pd.Timedelta(seconds=1)
    
    return pd.concat([df, first_df])



def get_first_statistics(df, id_col_name, activity_col_name, time_col_name):
    """
    This function determine statistics for each pairs of events in log  
    
    Parameters
    ----------
    df:                (pandas DataFrame) - log
    id_col_name:       (str)
    activity_col_name: (str)
    time_col_name:     (str)
    
    Returns
    -----------
    median_d:           (dict)  - median time for each pairs of events
    counts_d:           (dict)  - frequency for each pairs of events
    """
    df_init = initial_start_event(df, id_col_name, activity_col_name, time_col_name)
    df_init.sort_values([id_col_name, time_col_name], inplace=True)
    
    df_init["shift_event"] = df_init.groupby(id_col_name)[activity_col_name].shift(-1).fillna("end")
    df_init["shift_time"] = df_init.groupby(id_col_name)[time_col_name].shift(-1)
    df_init["time_delta"] = df_init["shift_time"] - df_init[time_col_name]
    
    median_d = dict(df_init.groupby([activity_col_name, "shift_event"])["time_delta"].describe()["50%"])
    counts_d = dict(df_init.value_counts([activity_col_name, "shift_event"]))
    
    return median_d, counts_d



def get_top_2_seq(ideal_seq, count_dict):
    """
    This fucntion return top 2 sequence (by counts) for each event in ideal_sequences
    
    Parameters
    -----------
    ideal_seq: (array) - sequence of ideal chain of process 
    count_dict: (dict) - counts for each sequences of log
    
    Returns
    -----------
    top_seq: (dict) - counts top 2 sequences with each event in ideal_seq
    
    """
    top_seq = dict()
    for evnt in ideal_seq:
        t_d = dict()
        for k in count_dict.keys():
            if k[0] == evnt:
                t_d[k] = count_dict[k]                                        ## [:2] top 2 sequences
        top_seq.update(dict(sorted(t_d.items(), key=lambda x: x[1], reverse=True)[:2]))
    
    return top_seq


def get_info_dict(ideal_seq, ideal_edges, median_dict, counts_dict):
    """
    This fucntion create dict with edge information, color and width 
    
    Parameters
    -----------
    
    ideal_seq: (array) - sequence of ideal chain of process 
    ideal_edges: (list of tuples) - edges, which get from ideal_seq
    median_dict: (dict) - dict with median time execution for each edges in log
    counts_dict: (dict) - dict with counts of edges in log
    
    Returns
    -----------
    
    info_dict, colors_d, width_d: (dicts) - info and parameters for each edge in log
    
    """
    info_dict = dict()
    colors_d = dict()
    width_d = dict()
    top_seq = get_top_2_seq(ideal_seq, counts_dict)
    for k in median_dict.keys():
        if k in ideal_edges:
            info_dict[k] = {"Initial event name of chosen sequence": k[0], 
                            "Final event name of chosen sequence": k[1],
                            "Initial event name of ideal sequence": k[0], 
                            "Final event name of ideal sequence": k[1],
                            "Median lead time of chosen sequence": str(median_dict[k]),
                            "Difference of median time between chosen and ideal sequence": "0 days",
                            "Frequency of chosen sequence": counts_dict[k],
                            "Proportion (frequency) from ideal sequence": "100 %"}
            colors_d[k] = "green"
            width_d[k] = 8
        else:
            t_flag = False
            for k_ideal in ideal_edges:
                if (k[0] == k_ideal[0]) | (k[1] == k_ideal[1]):
                    info_dict[k] = {"Initial event name of chosen sequence": k[0], 
                                    "Final event name of chosen sequence": k[1],
                                    "Initial event name of ideal sequence": k_ideal[0], 
                                    "Final event name of ideal sequence": k_ideal[1],
                                    "Median lead time of chosen sequence": str(median_dict[k]),
                                    
                                    'Difference of median time between chosen and ideal sequence':\
                                       f'{median_dict[k]-median_dict.get(k_ideal, pd.Timedelta("0 days 00:00:00"))}',
                                    
                                    "Frequency of chosen sequence": counts_dict[k],
                                    
                                    'Proportion (frequency) from ideal sequence':\
                                       f"{round(counts_dict[k]/counts_dict.get(k_ideal, counts_dict[k])*100, 2)} %"}
                    colors_d[k] = "orange"
                    width_d[k] = 1
                    t_flag = True
                    break
            if not t_flag:
                info_dict[k] = {"Initial event name of chosen sequence": k[0], 
                                "Final event name of chosen sequence": k[1],
                                "Initial event name of ideal sequence": "Полное отклонение от идеального процесса", 
                                "Final event name of ideal sequence": "Полное отклонение от идеального процесса",
                                "Median lead time of chosen sequence": str(median_dict[k]),
                                "Difference of median time between chosen and ideal sequence": "0 days",
                                "Frequency of chosen sequence": counts_dict[k],
                                "Proportion (frequency) from ideal sequence": "0 %"}
                colors_d[k] = "grey"
                width_d[k] = 1

        if (k in top_seq) & (k not in ideal_edges):
            colors_d[k] = "red"
            width_d[k] = 4

    return info_dict, colors_d, width_d



def create_html(info_dict, colors_d, width_d, html_name="Graph"):
    """
    This fucntion create html file with interactive graph of process 
    
    Parameters
    -----------
    
    info_dict: (dict) - information for each edge
    colors_d: (dict) - edges color
    width_d: (dict) - edges width
    html_name: (str) - 
    
    Returns
    -----------
    
    html file
    """
    from h_t import header_text
    from h_t import tail_text
    nodes = pd.unique([k_ for k in info_dict.keys() for k_ in k])
    word_num = dict()
    for c, word in enumerate(nodes):
        word_num[word] = c+1
        
    header_text += """\nvar nodes = new vis.DataSet([\n"""
    for w in nodes:
        if w == "start":
            color = "green"
            font = "28px arial"
        elif w == "end":
            color = "red"
            font = "28px arial"
        else:
            color = "#D2E5FF"
            font = "20px arial"
        header_text += "{"
        header_text += f"""         id: {word_num[w]},
                                    color: "{color}",
                                    label: "{w}",
                                    font: "{font}"\n"""
        header_text += "},"
    header_text += "   ]);\n"

    header_text += """var edges = new vis.DataSet(["""
    for k in info_dict.keys():
        header_text += "{"
        header_text += f"""       from: {word_num[k[0]]}, 
                        to: {word_num[k[1]]}, 
                        arrows: "to",
                        color: "{colors_d.get(k, "grey")}",
                        width: {width_d.get(k, 1)},
                        info: {info_dict[k]}\n"""
        header_text +="},"
    header_text += "   ]);\n"

    full_text = ""
    full_text += header_text
    full_text += tail_text

    with open(f"{html_name}.html", "w", encoding="utf-8") as f: 
        f.write(full_text)
