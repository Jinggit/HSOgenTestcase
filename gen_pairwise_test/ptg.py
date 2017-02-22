# Pair Wise Test Generator - PTG
import random

import re
import sys
import itertools
from ParameterType import Parameter
from ParameterInteractionStructure import ParameterInteractionStructure
from TestSet import *
from operator import methodcaller
from tabulate import tabulate

class genPairwisetestdata:
    def parse_input_file(self,file_path):
        """
        Remove comments from the .tile file and return a manageable set of data
        :param file_path: the full path of the file
        :return: a manageable set of data, list of hands as strings
        """
        """ Constants required to parse the input file """
        whitespace = re.compile(r'[ \f\t]*', re.DOTALL)
        single_line_comment = re.compile(r'((?://|#).*?\n)', re.DOTALL)
        multi_line_comment = re.compile("((?:(?:(?:\"|\'){3})|/\*).*?(?:(?:(?:\"|\'){3})|\*/))", re.DOTALL)
    
        string = re.sub(single_line_comment, '\n', open(file_path).read())  # Removes all single line comments
        string = re.sub(multi_line_comment, '', string)  # Removes multi-line comments
        string = re.sub(whitespace, '', string)  # Removes unnecessary whitespaces
        return [x for x in string.split("\n") if x is not '']
    
    def ifparamintemplist(self,param,temp_list):
        if param.split(":")[0] in temp_list:
            return True
        else:
            return False

    
    def main(self,file_path, temp_list, order=2):
        # ------------------------------------------------------------------------------------------------------------------
        # PREPARATION PHASE
        # ------------------------------------------------------------------------------------------------------------------
    
        file_contents = self.parse_input_file(file_path)
        # Declare regex constants that will match the template input arguments in file
        parameter_declaration_regex = re.compile("^\w+:\w+(,.*?)*$")
        # Get parameter declaration from file
        parameters = [Parameter(x) for x in file_contents if re.match(parameter_declaration_regex, x) and self.ifparamintemplist(x,temp_list)]
        #print parameters

        print parameters
            
        if len(parameters) > 1:           
            parameters_seq = []
            for temp in temp_list:
                for param in parameters:
                    if temp == str(param).split(":")[0]:
                        parameters_seq.append(param)
            parameters = parameters_seq
            # Generate parameter interaction objects
            pi_list = []
            for combination in itertools.combinations(parameters, order):
                pi_list.append(ParameterInteractionStructure(combination))
        
            # ------------------------------------------------------------------------------------------------------------------
            # GENERATION PHASE
            # ------------------------------------------------------------------------------------------------------------------
        
            # Initialize TestSet.py to be empty # TODO - In the future must support seeds
            result_set = []
        
            """ LEGEND:
                pi_obj := Parameter Interaction Object
                pi_list := Parameter Interaction List
            """
        
            all_slots = [tuple(slot.data) for slot in list(itertools.chain(*[pi_obj.get_slots() for pi_obj in pi_list]))]
            slot_tracking = dict([(tup, True) for tup in all_slots])
        
            while any([not pi_obj.is_covered() for pi_obj in pi_list]):
        
                cur_tc = TestCase(parameters)
                # Pick the first uncovered slot from parameter_interaction with most uncovered slots
                best_slot = max(pi_list, key=methodcaller('get_uncovered_slots_count')).get_next_slot()
                best_slot.set_covered()  # Set slot to covered = True
                cur_tc.add_slot(best_slot)
        
                while None in cur_tc:  # While test case is not full
        
                    uncovered_param_set = cur_tc.get_uncovered_parameters_set()
                    # Q holds parameter interaction structures with parameters yet uncovered in the test case
                    Q = (pi_obj for pi_obj in pi_list if any(p in pi_obj.get_params_set() for p in uncovered_param_set))
                    # Uncovered slots in Q which values are consistent with already chosen values in the test case
                    Q_slot_list = list(itertools.chain(*[pi_obj.get_slots() for pi_obj in Q]))
        
                    # set containing values added to test case and all values of pi_obj to be covered
                    values_set = set(itertools.chain(*[p.get_values_list() for p in uncovered_param_set])).union(
                        cur_tc.get_values_list())
        
                    slot_lookup_pool = [s for s in Q_slot_list if slot_tracking[tuple(s.data)] and all([v in values_set for v in s])]
        
                    if slot_lookup_pool:  # If not empty, there exist uncovered combinations
                        max_count = 0
                        covered_slot_list = None
                        # best_slot will cover max count of uncovered combinations
                        for slot in slot_lookup_pool:
                            values = set(cur_tc.get_values_list()).union(set(slot.data))
                            covered_slots = [s for s in all_slots if set(s).issubset(values) and slot_tracking[tuple(slot)]]
                            covered_count = len(covered_slots)
                            if covered_count > max_count:
                                max_count = covered_count
                                best_slot = slot
                                covered_slot_list = covered_slots
                        # Set all slots covered by best_slot to covered == True
                        for slot in covered_slot_list:
                            slot_tracking[tuple(slot)] = False
        
                    # All slots have been covered, pick a random slot which when added to
                    # test_case would not contain any excluded combination
                    else:
                        slot_lookup_pool = [s for s in Q_slot_list if all([v in values_set for v in s])]
                        if slot_lookup_pool:
                            best_slot = random.choice(slot_lookup_pool)
                    cur_tc.add_slot(best_slot)
                    best_slot.set_covered()
                result_set.append(cur_tc)
            results = self.print_result(result_set, parameters,temp_list)
            print results
            return results
        
        elif len(parameters) == 1 and len(str(parameters[0]).split(":")[1].split(",")) == 1:
            return [str(parameters[0]).split(":")[1].split(",")]
        
        elif len(parameters) == 1 and len(str(parameters[0]).split(":")[1].split(",")) > 1:
            return [[i] for i in str(parameters[0]).split(":")[1].split(",")]
            
        else:
            return []
    
    
    def print_result(self,result_set, parameters,temp_list):
        headers = [param.get_name() for param in parameters]
        #print headers
        val_translation_map = dict()
        results=[]
        for d in [param.get_value_dict() for param in parameters]:
            val_translation_map.update(d)
            #results = [headers]
        for test_case in result_set:
            results.append([val_translation_map[i] for i in test_case.tc_array])
        return results
        #print(tabulate(results))
        #print("The count of tests is : ", len(results)-1)
         

if __name__ == "__main__":
    gp = genPairwisetestdata()
    gp.main('./input-file.txt',['baseId','count','isRefresh', 'roomId'])
    #gp.main('./input-file.txt',['account','password'])
        
