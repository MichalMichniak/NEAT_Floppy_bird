import random
from typing import List,Callable,Dict
import numpy as np
from copy import deepcopy
import random
class Connection:
    def __init__(self, input_neuron, output_neuron, weight, innovation_nr = 0, disabled_enabled = True):
        self.input_neuron = input_neuron
        self.output_neuron = output_neuron
        self.weight = weight
        self.disabled_enabled = disabled_enabled
        #self.innovation_number = innovation_nr
        self.is_feedforward = False
        self.state = 0
    def __repr__(self):
        return f"({self.input_neuron},{self.output_neuron}) w{self.weight},{'F' if self.is_feedforward else 'R'}"
    def get_out(self):
        return self.weight*self.state
    def __str__(self) -> str:
        return f"{self.input_neuron},{self.output_neuron}"

class Net:
    """
    with recurent connections
    """
    def __init__(self,nr_inputs : List[int], nr_outputs : List[int], nr_neurons : List[int] , connections : List[Connection], activation_func : Callable[[float],float] = None):
        self.neurons = nr_neurons
        self.nr_inputs = nr_inputs
        self.nr_outputs = nr_outputs
        self.connections = connections
        dict_of_output_conn : Dict[int,List[Connection]] = {i:[] for i in self.nr_inputs+self.neurons+self.nr_outputs}
        dict_of_input_conn : Dict[int,List[Connection]] = {i:[] for i in self.nr_inputs+self.neurons+self.nr_outputs}
        for i in range(len(self.connections)):
            dict_of_output_conn[self.connections[i].input_neuron].append(self.connections[i])
            dict_of_input_conn[self.connections[i].output_neuron].append(self.connections[i])
        if activation_func == None:
            activation_func = lambda x: 1/(1+np.exp(-x))
        self.activation_func = activation_func
        self.propagation_arrangement = self.nr_inputs.copy()
        ## detection of feedforward and recurent connections
        """
        sth like graph traversation but next edge is chosed among edges with least 
        recurent connections so far
        """
        visited = {i : False for i in self.nr_inputs+self.neurons+self.nr_outputs}
        recurent = {i : 0 for i in self.nr_inputs+self.neurons+self.nr_outputs}
        for co in self.connections:
            recurent[co.output_neuron] +=1
        lst = []
        for i in self.nr_inputs:
            visited[i] = True
            for j in range(len(dict_of_output_conn[i])):
                dict_of_output_conn[i][j].is_feedforward = True
                recurent[dict_of_output_conn[i][j].output_neuron] -= 1
                if dict_of_output_conn[i][j].output_neuron not in lst:
                    lst.append(dict_of_output_conn[i][j].output_neuron)
        
        while lst != []:
            recurent_count = [recurent[i] for i in lst]
            idx = recurent_count.index(min(recurent_count))
            temp = idx
            idx = lst[idx]
            lst.pop(temp)
            visited[idx] = True
            self.propagation_arrangement.append(idx)
            for j in range(len(dict_of_output_conn[idx])):
                dict_of_output_conn[idx][j].is_feedforward = True
                recurent[dict_of_output_conn[idx][j].output_neuron] -= 1
                if (dict_of_output_conn[idx][j].output_neuron not in lst) and (not visited[idx]):
                    lst.append(dict_of_output_conn[idx][j].output_neuron)
        self.dict_of_output_conn = dict_of_output_conn
        self.dict_of_input_conn = dict_of_input_conn

        self.list_of_non_disabled_conn = []
        for i in self.connections:
            if i.disabled_enabled:
                self.list_of_non_disabled_conn.append(i)



    def count(self, input):
        out = []
        for in_neur_idx in range(len(self.nr_inputs)):
            nuron_tag = self.nr_inputs[in_neur_idx]
            for i in range(len(self.dict_of_output_conn[nuron_tag])):
                if self.dict_of_output_conn[nuron_tag][i].disabled_enabled:
                    self.dict_of_output_conn[nuron_tag][i].state = self.activation_func(input[in_neur_idx])
        for current_neuron in self.propagation_arrangement[len(input):-len(self.nr_outputs)]:
            ## biases here \/\/\/\/
            signal = 0
            for i in  range(len(self.dict_of_input_conn[current_neuron])):
                if self.dict_of_input_conn[current_neuron][i].disabled_enabled:
                    signal += self.dict_of_input_conn[current_neuron][i].get_out()
            for i in  range(len(self.dict_of_output_conn[current_neuron])):
                if self.dict_of_output_conn[current_neuron][i].disabled_enabled:
                    self.dict_of_output_conn[current_neuron][i].state = self.activation_func(signal)
            pass
        for current_neuron in self.propagation_arrangement[-len(self.nr_outputs):]:
            ## biases here \/\/\/\/
            signal = 0
            for i in  range(len(self.dict_of_input_conn[current_neuron])):
                if self.dict_of_input_conn[current_neuron][i].disabled_enabled:
                    signal += self.dict_of_input_conn[current_neuron][i].get_out()
            out.append(self.activation_func(signal))
        return out

    def zero_state(self):
        for i in range(len(self.connections)):
            self.connections[i].state = 0





class Control:
    def __init__(self,n_inputs, n_outputs, net = None) -> None:
        self.n_inputs = n_inputs
        self.n_outputs = n_outputs
        if net == None:
            self.conn = [Connection(0,4,random.uniform(-6,6),0),Connection(1,4,random.uniform(-0.03,0.03),1),Connection(2,4,random.uniform(-0.03,0.03),2),Connection(3,4,random.uniform(-6,6),3)]
            self.net = Net([0,1,2,3],[4],[],self.conn)
        else:
            self.net = deepcopy(net)
        pass

    def predict(self, input):
        if input[2] < 0:
            return 1
        else:
            return 0

    def predict(self, input):
        out = self.net.count(input)
        return out[0] >= 0.5



if __name__ == '__main__':

    conn = [Connection(0,4,random.uniform(-6,6),0),Connection(1,4,random.uniform(-0.03,0.03),1),Connection(2,4,random.uniform(-0.03,0.03),2),Connection(3,4,random.uniform(-6,6),3)]
    net = Net([0,1,2,3],[4],[],conn)
    print(net.count([0,0,0,0]))
    pass