import pandas as pd
import numpy as np

def predict_protein_location_1epoch(proteins):

    predicted_gene_list = []
    predicting_gene_list = []
    crosslinks_list = []
    predicted_by_transmembrane_list = []
    predicted_location_list = []

    proteins['crosslinks'] = proteins['crosslinks'].fillna("")
    for i in proteins.index:
        if pd.isna(proteins.iloc[i]['subcellular_location']):
            continue

        gene = proteins.iloc[i]['gene']
        sl = proteins.iloc[i]['subcellular_location']

        crosslinks_raw = proteins.iloc[i]['crosslinks']

        crosslinks = crosslinks_raw.split("#")
        for j in crosslinks:
            link = j.split('-')
            if len(link) < 4:
                continue
            gene_b = link[2]

            predicted_gene_list.append(gene_b)
            predicting_gene_list.append(gene)
            crosslinks_list.append(j)
            predicted_location_list.append(sl)

            if pd.isna(proteins.iloc[i]['transmembrane']):
                predicted_by_transmembrane_list.append(np.nan)
            else:
                predicted_by_transmembrane_list.append(proteins.iloc[i]['transmembrane'])

    new_data = pd.DataFrame({'predicted_gene': predicted_gene_list, 'predicting_gene': predicting_gene_list,
                             'predicted_location': predicted_location_list,
                             'predicting_crosslinks': crosslinks_list,
                             'predicted_by_transmembrane': predicted_by_transmembrane_list})

    return new_data

def combine_predicted_information(proteins,combined_data):
    gene_helper_list = []

    predicted_gene_list = []
    predicting_gene_list = []
    predicting_gene_residue_list = []
    predicted_gene_residue_list = []
    crosslinks_list = []
    predicted_by_transmembrane_list = []
    predicted_location_list = []
    transmembrane_regions_list = []

    combined_data['transmembrane'] = combined_data['transmembrane'].fillna("")
    for i in proteins.index:
        gene = proteins.iloc[i]['predicted_gene']

        tms_combined = ""

        if gene in gene_helper_list:
            continue

        gene_helper_list.append(gene)

        tms = combined_data.loc[combined_data['gene'] == gene]
        for k in list(range(tms.shape[0])):
            t = tms.iloc[k]['transmembrane']
            if t != "" and tms_combined == "":
                tms_combined = ',' + t
            elif t != "" and tms_combined != "":
                tms_combined = tms_combined + ',' + t

        sub = proteins.loc[proteins['predicted_gene'] == gene]

        for j in list(range(sub.shape[0])):
            xlink = sub.iloc[j]['predicting_crosslinks']
            xlink_split = xlink.split('-')

            if 'ND' in xlink_split[3] or 'ATP' in xlink_split[3]:
                continue

            predicted_gene_list.append(gene)
            predicted_gene_residue_list.append(int(xlink_split[3]))
            predicting_gene_residue_list.append(int(xlink_split[1]))
            predicting_gene_list.append(sub.iloc[j]['predicting_gene'])
            predicted_location_list.append(sub.iloc[j]['predicted_location'])
            crosslinks_list.append(sub.iloc[j]['predicting_crosslinks'])
            predicted_by_transmembrane_list.append(sub.iloc[j]['predicted_by_transmembrane'])
            transmembrane_regions_list.append(tms_combined)

    new_data = pd.DataFrame({'predicted_gene': predicted_gene_list, 'predicting_gene': predicting_gene_list,
                             'predicted_gene_residue': predicted_gene_residue_list,
                             'predicting_gene_residue': predicting_gene_residue_list,
                             'predicted_location': predicted_location_list,
                             'predicting_crosslinks': crosslinks_list,
                             'predicted_by_transmembrane': predicted_by_transmembrane_list,
                             'transmembrane_regions': transmembrane_regions_list})

    return new_data

# function update crosslinks in proteins according to transmembrane regions
def update_xlinks_transmembrane(combined_data):
    gene_helper_list = []

    gene_list = []
    protein_list = []
    location_list = []
    crosslinks_list = []
    transmembrane_list = []

    combined_data['transmembrane'] = combined_data['transmembrane'].fillna('')
    combined_data['crosslinks'] = combined_data['crosslinks'].fillna("")
    combined_data['subcellular_location'] = combined_data['subcellular_location'].fillna("")
    for i in combined_data.index:
        gene = combined_data.iloc[i]['gene']
        protein = combined_data.iloc[i]['protein']

        if gene in gene_helper_list:
            continue

        gene_helper_list.append(gene)

        sub = combined_data.loc[combined_data['gene'] == gene]

        xlinks = sub.loc[sub['crosslinks'] != '']
        joined_xlinks = xlinks.crosslinks.str.cat(sep='#')
        crosslinks_split = joined_xlinks.split('#')

        if joined_xlinks == '':
            gene_list.extend(sub.gene)
            protein_list.extend(sub.protein)
            location_list.extend(sub.subcellular_location)
            crosslinks_list.extend(sub.crosslinks)
            transmembrane_list.extend(sub.transmembrane)
            continue

        if (sub.transmembrane != '').sum() == 0:
            gene_list.append(gene)
            protein_list.append(protein)
            location_list.append(sub.iloc[0]['subcellular_location'])
            crosslinks_list.append(sub.iloc[0]['crosslinks'])
            transmembrane_list.append(sub.iloc[0]['transmembrane'])

        elif (sub.transmembrane != '').sum() == 1:
            # get crosslinks before and after and order them new
            reg = sub.loc[sub['transmembrane'] != '', 'transmembrane'].values[0]

            region = reg.split('..')

            crosslinks_before_tm = []
            crosslinks_after_tm = []
            crosslinks_in_tm = []

            transmem_start = int(region[0])
            transmem_end = int(region[1])
            for k in crosslinks_split:
                link = k.split('-')
                if link[1] == 'ATP6' or link[1] == 'ND1':
                    continue
                if int(link[1]) < transmem_start:
                    crosslinks_before_tm.append(k)
                elif int(link[1]) > transmem_end:
                    crosslinks_after_tm.append(k)
                elif transmem_end >= int(link[1]) >= transmem_start:
                    crosslinks_in_tm.append(k)
            # concatenate list and add them
            gene_list.extend((gene, gene, gene))
            protein_list.extend((protein, protein, protein))
            location_list.extend((sub.iloc[0]['subcellular_location'], np.nan, sub.iloc[2]['subcellular_location']))
            crosslinks_list.extend(
                ('#'.join(crosslinks_before_tm), '#'.join(crosslinks_in_tm), '#'.join(crosslinks_after_tm)))
            transmembrane_list.extend((np.nan, reg, np.nan))

        elif (sub.transmembrane != '').sum() > 1:
            transmem_regions = sub.loc[sub['transmembrane'] != '', 'transmembrane'].values


            for j in range(len(transmem_regions)):
                transmem_all = transmem_regions[j].split('..')
                transmem_start = int(transmem_all[0])
                transmem_end = int(transmem_all[1])

                # location before transmembrane region
                index_transmembrane = sub.index[sub['transmembrane'] == transmem_regions[j]].tolist()
                location_before = sub.loc[index_transmembrane[0]-1]['subcellular_location']
                # location after transmembrane region
                location_after = sub.loc[index_transmembrane[0] + 1]['subcellular_location']

                crosslinks_before_tm = []
                crosslinks_after_tm = []
                crosslinks_in_tm = []
                # get all crosslinks

                if transmem_regions[j] == transmem_regions[0]:
                    for k in crosslinks_split:
                        link = k.split('-')
                        if link[1] == 'ATP6' or link[1] == 'ND1':
                            continue
                        if int(link[1]) < transmem_start:
                            crosslinks_before_tm.append(k)
                        elif transmem_end >= int(link[1]) >= transmem_start:
                            crosslinks_in_tm.append(k)
                elif transmem_regions[j] != transmem_regions[0] and transmem_regions[j] != transmem_regions[
                    len(transmem_regions) - 1]:
                    transmem_before = transmem_regions[j - 1].split('..')
                    transmem_before_end = int(transmem_before[1])

                    transmem_after = transmem_regions[j + 1].split('..')
                    transmem_after_start = int(transmem_after[1])

                    for k in crosslinks_split:
                        link = k.split('-')
                        if link[1] == 'ATP6' or link[1] == 'ND1':
                            continue
                        # also before and after will be the same if there are multiple transmembrane regions
                        if transmem_start > int(link[1]) > transmem_before_end:
                            crosslinks_before_tm.append(k)

                        elif (int(link[1]) > transmem_end) and (int(link[1]) < transmem_after_start):
                            crosslinks_after_tm.append(k)
                        elif transmem_end >= int(link[1]) >= transmem_start:
                            crosslinks_in_tm.append(k)
                elif transmem_regions[j] == transmem_regions[len(transmem_regions) - 1]:
                    transmem_before = transmem_regions[j - 1].split('..')
                    transmem_before_end = int(transmem_before[1])

                    for k in crosslinks_split:
                        link = k.split('-')
                        if link[1] == 'ATP6' or link[1] == 'ND1':
                            continue
                        # also before and after will be the same if there are multiple transmembrane regions
                        if transmem_start > int(link[1]) > transmem_before_end:
                            crosslinks_before_tm.append(k)
                        elif int(link[1]) > transmem_end:
                            crosslinks_after_tm.append(k)
                        elif transmem_end >= int(link[1]) >= transmem_start:
                            crosslinks_in_tm.append(k)
                # concatenate list and add them
                gene_list.extend((gene, gene, gene))
                protein_list.extend((protein, protein, protein))
                location_list.extend((location_before, np.nan, location_after))
                crosslinks_list.extend(
                    ('#'.join(crosslinks_before_tm), '#'.join(crosslinks_in_tm), '#'.join(crosslinks_after_tm)))
                transmembrane_list.extend((np.nan, transmem_regions[j], np.nan))


    new_data = pd.DataFrame({'gene': gene_list, 'protein': protein_list,
                             'subcellular_location': location_list,
                             'crosslinks': crosslinks_list,
                             'transmembrane': transmembrane_list})

    return new_data

if __name__ == '__main__':
    combined_data = pd.read_csv('combined_data.csv')

    data = update_xlinks_transmembrane(combined_data)
    # predict protein location
    predicted_proteins = predict_protein_location_1epoch(combined_data)

    result = combine_predicted_information(predicted_proteins,combined_data)

    result2 = result.sort_values(by=['predicted_gene','predicted_gene_residue'], ascending=True)
    result2.reset_index().to_csv('prediction_result.csv',index=False)

    print('done')