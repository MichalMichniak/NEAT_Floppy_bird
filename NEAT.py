from control import Net
from control import Connection
from typing import List
import random
from copy import deepcopy
from floppy_with_control import Flopy_control

from control import Control
X_FLOPY = 50
class NEAT:
    def __init__(self):
        """
        convention nr of neurons starts with inputs then outputs next are additional neurons
        """
        self.dictionary_of_connections = {"0,4":0,"1,4":1,"2,4":2,"3,4":3}
        self.next_innovation_nr = 4
        self.mutation_connection_probability = 0.2
        self.mutation_neuron_probability = 0.005
        self.mutation_weight_probability = 1 - self.mutation_connection_probability - self.mutation_neuron_probability
        self.input_neurons_nr = [0,1,2,3]
        self.output_neurons_nr = [4]
        self.additional_neurons = []
        ## Speciation params:
        self.c1 = 1.0
        self.c2 = 1.0
        self.c3 = 0.5
        self.species_treshold = 4
        self.max_species = 6


    def evolve_population(self, lst_insta : List[Flopy_control], score_avg = False):
        if score_avg:
            for i in range(len(lst_insta)):
                if lst_insta[i].survived_rounds == 0:
                    lst_insta[i].avg_score = lst_insta[i].score
                    lst_insta[i].survived_rounds += 1
                else:
                    lst_insta[i].avg_score = (lst_insta[i].avg_score*lst_insta[i].survived_rounds + lst_insta[i].score)/(lst_insta[i].survived_rounds + 1)
                    lst_insta[i].survived_rounds += 1
            lst_insta.sort(key= lambda x: x.avg_score, reverse=True)
        else:
            lst_insta.sort(key= lambda x: x.score, reverse=True)
        
        #Speciation
        species_lst : List[List[Flopy_control]] = []
        species_lst.append([lst_insta[0]])
        for i in range(1,len(lst_insta)):
            for j in range(len(species_lst)):
                if self.compare(lst_insta[i].control_.net,species_lst[j][0].control_.net) < self.species_treshold:
                    species_lst[j].append(lst_insta[i])
                    break
            else:
                species_lst.append([lst_insta[i]])
        
        ## count fitness function for each population:
        avg_score = [0 for i in range(len(species_lst))]
        for i in range(len(species_lst)):
            for j in range(len(species_lst[i])):
                if score_avg:
                    avg_score[i]+=species_lst[i][j].avg_score+1
                else:
                    avg_score[i]+=species_lst[i][j].score+1
            avg_score[i]=avg_score[i]/(len(species_lst[i]))

        pop_count = len(lst_insta)
        ## half the population of each species
        
        for i in range(len(species_lst)):
            if len(species_lst[i]) == 1:
                r = random.randint(0,1)
                if r == 1:
                    species_lst[i] = []
            else:
                species_lst[i] = species_lst[i][:len(species_lst[i])//2]
        
        i = 0
        while i != len(species_lst):
            if species_lst[i] == []:
                avg_score.pop(i)
                species_lst.pop(i)
                i-=1
            i+=1
        if len(species_lst) > self.max_species:
            execute = len(species_lst) - self.max_species
            for i in range(execute):
                idx = avg_score.index(min(avg_score))
                avg_score.pop(idx)
                species_lst.pop(idx)
        
        total_population = 0
        for i in range(len(species_lst)):
            total_population += len(species_lst[i])
        
        generate_nr = pop_count - total_population


        normalised_avg_score = [(i/sum(avg_score) if sum(avg_score)!= 0 else 0)  for i in avg_score]
        to_generate = [round(normalised_avg_score[i]*generate_nr - 0.00000001) for i in range(len(normalised_avg_score))]
        rest = pop_count - total_population - sum(to_generate)
        to_generate[0] += rest
        lst_insta = []
        for i in range(len(species_lst)):
            lst_insta.extend(species_lst[i])
        
        ## crossing & mutation
        for i in range(len(to_generate)):
            for j in range(to_generate[i]):
                if len(species_lst[i]) == 1:
                    new_network = self.mutate(self.cross(species_lst[i][0].control_.net,species_lst[i][0].control_.net))
                    lst_insta.append(Flopy_control(X_FLOPY,250+random.randint(-120,120),Control(len(self.input_neurons_nr),len(self.output_neurons_nr),new_network)))
                else:
                    r1 = random.randint(0,len(species_lst[i])-1)
                    r2 = random.randint(0,len(species_lst[i])-1)
                    new_network = self.mutate(self.cross(species_lst[i][r1].control_.net,species_lst[i][r2].control_.net))
                    lst_insta.append(Flopy_control(X_FLOPY,250+random.randint(-120,120),Control(len(self.input_neurons_nr),len(self.output_neurons_nr),new_network)))
        print(f"number of species: {len(species_lst)} , population: {len(lst_insta)}")
        return lst_insta
    
    def mutate(self, insta : Net)-> Net:
        p = random.uniform(0,1)
        list_of_conn = deepcopy(insta.connections)
        list_of_neurons = deepcopy(insta.neurons)
        if p < self.mutation_neuron_probability:
            # neuron addition
            r = random.randint(0,len(insta.list_of_non_disabled_conn)-1)
            if self.additional_neurons == []:
                neuron_nr = self.output_neurons_nr[-1]+1
            else:
                neuron_nr = self.additional_neurons[-1] +1
            self.additional_neurons.append(neuron_nr)
            list_of_conn[r].disabled_enabled = False
            ## neuron with highest number always last
            list_of_neurons.append(neuron_nr)
            ## connection with highest innovation number always last
            conn1 = f"{list_of_conn[r].input_neuron},{neuron_nr}"
            list_of_conn.append(Connection(list_of_conn[r].input_neuron,neuron_nr,list_of_conn[r].weight))
            conn2 = f"{neuron_nr},{list_of_conn[r].output_neuron}"
            list_of_conn.append(Connection(neuron_nr,list_of_conn[r].output_neuron,list_of_conn[r].weight))
            self.dictionary_of_connections[conn1] = self.next_innovation_nr
            self.next_innovation_nr+=1
            self.dictionary_of_connections[conn2] = self.next_innovation_nr
            self.next_innovation_nr+=1

        elif p < self.mutation_connection_probability + self.mutation_neuron_probability:
            # connection addition 
            n1 = random.randint(0,len(list_of_neurons)+len(self.input_neurons_nr)-1)
            n2 = random.randint(len(self.input_neurons_nr),len(list_of_neurons)+len(self.input_neurons_nr)+len(self.output_neurons_nr)-1)
            n1 = (self.input_neurons_nr + list_of_neurons + self.output_neurons_nr)[n1]
            n2 = (self.input_neurons_nr + list_of_neurons + self.output_neurons_nr)[n2]
            if f"{n1},{n2}" in self.dictionary_of_connections.keys():
                ## it can be done by bisection O(log n) but through linear search O(n)
                for i in list_of_conn:
                    if str(i) == f"{n1},{n2}":
                        p+=1
                        break
                else:
                    for i in range(len(list_of_conn)):
                        if self.dictionary_of_connections[str(list_of_conn[i])] > self.dictionary_of_connections[f"{n1},{n2}"]:
                            list_of_conn.insert(i,Connection(n1,n2,0.0001))
                            break
                    else:
                        list_of_conn.append(Connection(n1,n2,0.0001))
            else:
                self.dictionary_of_connections[f"{n1},{n2}"] = self.next_innovation_nr
                self.next_innovation_nr+=1
                list_of_conn.append(Connection(n1,n2,0.0001))

        if p>=self.mutation_connection_probability + self.mutation_neuron_probability:
            if len(insta.list_of_non_disabled_conn)-1 == -1:
                pass
            elif len(insta.list_of_non_disabled_conn)-1 == 0:
                list_of_conn[0].weight += random.uniform(-1,1)
            else:
                r = random.randint(0,len(insta.list_of_non_disabled_conn)-1)
                list_of_conn[r].weight += random.uniform(-1,1)
            pass
        return Net(deepcopy(self.input_neurons_nr),deepcopy(self.output_neurons_nr),list_of_neurons,list_of_conn)


    def cross(self, parent1 : Net,parent2 : Net):
        list_of_conn1 = deepcopy(parent1.connections)
        list_of_neurons1 = deepcopy(parent1.neurons)
        list_of_conn2 = deepcopy(parent2.connections)
        list_of_neurons2 = deepcopy(parent2.neurons)
        list_of_neurons = list(set(list_of_neurons1+list_of_neurons2))
        list_of_conn = []
        run = True
        conn1_idx = 0
        conn2_idx = 0
        while run:
            if self.dictionary_of_connections[str(list_of_conn1[conn1_idx])] > self.dictionary_of_connections[str(list_of_conn2[conn2_idx])]:
                list_of_conn.append(list_of_conn2[conn2_idx])
                conn2_idx+=1
            elif self.dictionary_of_connections[str(list_of_conn1[conn1_idx])] < self.dictionary_of_connections[str(list_of_conn2[conn2_idx])]:
                list_of_conn.append(list_of_conn1[conn1_idx])
                conn1_idx+=1
            else:
                # check if any of genes sleep and chose 50%
                genne1 = list_of_conn1[conn1_idx]
                genne2 = list_of_conn2[conn2_idx]
                if genne1.disabled_enabled != genne2.disabled_enabled:
                    if genne1.disabled_enabled:
                        list_of_conn.append(list_of_conn1[conn1_idx])
                    else:
                        list_of_conn.append(list_of_conn2[conn2_idx])
                else:
                    r = random.randint(0,1)
                    if r == 0:
                        list_of_conn.append(list_of_conn1[conn1_idx])
                    else:
                        list_of_conn.append(list_of_conn2[conn2_idx])
                conn1_idx+=1
                conn2_idx+=1
            if conn2_idx == len(list_of_conn2) and conn1_idx == len(list_of_conn1):
                run = False
            elif conn2_idx == len(list_of_conn2):
                list_of_conn.extend(list_of_conn1[conn1_idx:])
                run = False
            elif conn1_idx == len(list_of_conn1):
                list_of_conn.extend(list_of_conn2[conn2_idx:])
                run = False
        return Net(deepcopy(self.input_neurons_nr),deepcopy(self.output_neurons_nr),list_of_neurons,list_of_conn)

    def compare(self, net1 : Net, net2 : Net):
        w_diff = 0
        excess = 0
        disjoint = 0
        list_of_conn1 = net1.connections
        list_of_conn2 = net2.connections
        n = max(len(list_of_conn1),len(list_of_conn2))
        conn_net1_idx = 0
        conn_net2_idx = 0
        run = True
        while run:
            if self.dictionary_of_connections[str(list_of_conn1[conn_net1_idx])] > self.dictionary_of_connections[str(list_of_conn2[conn_net2_idx])]:
                disjoint += 1
                conn_net2_idx+=1
            elif self.dictionary_of_connections[str(list_of_conn1[conn_net1_idx])] < self.dictionary_of_connections[str(list_of_conn2[conn_net2_idx])]:
                disjoint += 1
                conn_net1_idx+=1
            else:
                w_diff += abs(list_of_conn1[conn_net1_idx].weight - list_of_conn2[conn_net2_idx].weight)
                conn_net1_idx+=1
                conn_net2_idx+=1
        
            if conn_net2_idx == len(list_of_conn2) and conn_net1_idx == len(list_of_conn1):
                run = False
            elif conn_net2_idx == len(list_of_conn2):
                excess = len(list_of_conn1[conn_net1_idx:])
                run = False
            elif conn_net1_idx == len(list_of_conn1):
                excess = len(list_of_conn2[conn_net2_idx:])
                run = False
        return (self.c1*excess/n)+(self.c2*disjoint/n) + (self.c3*w_diff)