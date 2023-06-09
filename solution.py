import csv
import math

from bnetbase import Variable, Factor, BN, adultDatasetBN
import itertools


def multiply_factors(Factors):
    '''Factors is a list of factor objects.
    Return a new factor that is the product of the factors in Factors.
    @return a factor'''
    ### YOUR CODE HERE ###

    variable_lst = []  # a list used to record all variables for all factors.
    domain_value_lst = []  # a list used to record all domain values for all variables in all factors.

    dict = {}
    for factor in Factors:
        scope = factor.get_scope()
        for variable in scope:
            dict[variable] = variable.dom
    variable_lst = list(dict.keys())
    domain_value_lst = list(dict.values())

    # add variable lst to the new Factor obj.
    new_factor = Factor("multiply_factor", variable_lst)

    # all the combinations of each variable's domain values
    outcomes = list(itertools.product(*domain_value_lst))

    # do the product

    for outcome in outcomes:
        # print(outcome)
        count = 0
        result = 1
        for v in outcome:
            # variable_lst[count].set_evidence(v)
            variable_lst[count].set_assignment(v)
            count += 1

        for factor in Factors:
            # print("???", factor.get_value_at_current_assignments())
            result *= factor.get_value_at_current_assignments()
            # print("result", result)
        new_factor.add_value_at_current_assignment(result)

    return new_factor


def restrict_factor(f, var, value):
    '''f is a factor, var is a Variable, and value is a value from var.domain.
    Return a new factor that is the restriction of f by this var = value.
    Don't change f! If f has only one variable its restriction yields a
    constant factor.
    @return a factor'''
    ### YOUR CODE HERE ###
    value_list = []
    # constant factor case
    if var not in f.scope:
        return f
    else:
        variable_lst = f.get_scope()
        index = variable_lst.index(var)
        for variable in variable_lst:
            value_list.append(variable.dom)
        variable_lst.remove(var)
        value_list[index] = [value]
        # get all possible combinations of the var and restricting variable.
        outcomes = list(itertools.product(*value_list))

        # create a new factor obj
        new_factor = Factor("restrict_factor", variable_lst)

        outcome_list = tuple_to_list(outcomes)

        for outcome in outcome_list:
            new_value = f.get_value(outcome)
            outcome.remove(value)
            outcome.append(new_value)
            values = [outcome]
            new_factor.add_values(values)
        return new_factor


def tuple_to_list(lst):
    lst1 = []
    for item in lst:
        lst1.append(list(item))
    return lst1


def sum_out_variable(f, var):
    '''f is a factor, var is a Variable.
    Return a new factor that is the result of summing var out of f, by summing
    the function generated by the product over all values of var.
    @return a factor'''
    ### YOUR CODE HERE ###

    allvar_lst = f.get_scope()
    index = allvar_lst.index(var)
    var_list = []
    var_dom = []
    for variable in allvar_lst:
        if variable != var:
            var_list.append(variable)
            var_dom.append(variable.dom)
    outcomes = list(itertools.product(*var_dom))
    outcome_lst = tuple_to_list(outcomes)
    new_factor = Factor("sum_out_variable", var_list)
    lst = []
    for outcome in outcome_lst:
        count = 0
        result = 0
        for value in outcome:
            var_list[count].set_evidence(value)
            var_list[count].set_assignment(value)
            count += 1
        for v in var.dom:
            outcome.insert(index, v)
            result += f.get_value(outcome)
            outcome.pop(index)

        new_factor.add_value_at_current_assignment(result)
    # print(new_factor.values)
    return new_factor


def normalize(nums):
    '''num is a list of numbers. Return a new list of numbers where the new
    numbers sum to 1, i.e., normalize the input numbers.
    @return a normalized list of numbers'''
    ### YOUR CODE HERE ###
    lst = []
    input_sum = sum(nums)
    for num in nums:
        if num == 0:
            lst.append(num)
        else:
            lst.append(abs(num / input_sum))
    return lst


def min_fill_ordering(Factors, QueryVar):
    '''Factors is a list of factor objects, QueryVar is a query variable.
    Compute an elimination order given list of factors using the min fill heuristic. 
    Variables in the list will be derived from the scopes of the factors in Factors. 
    Order the list such that the first variable in the list generates the smallest
    factor upon elimination. The QueryVar must NOT part of the returned ordering list.
    @return a list of variables'''
    ### YOUR CODE HERE ###
    variable_lst = []
    min_fill_order = []

    min_lst = []
    for factor in Factors:
        scope = factor.get_scope()
        min_lst.append(len(scope))

    minimum_length = min(min_lst)

    for factor in Factors:
        scope = factor.get_scope()
        if len(scope) == minimum_length:
            if scope[0] != QueryVar:
                variable_lst.append(scope[0])

    while len(variable_lst) != 0:
        min_variable = None
        min_value = float("inf")
        for variable in variable_lst:
            num = 0
            for factor in Factors:
                scope = factor.get_scope()
                if variable in scope:
                    num += 1
            if num < min_value:
                min_value = num
                min_variable = variable

        min_fill_order.append(min_variable)
        variable_lst.remove(min_variable)
    # print(min_fill_order)
    return min_fill_order


def VE(Net, QueryVar, EvidenceVars):
    """
    Input: Net---a BN object (a Bayes Net)
           QueryVar---a Variable object (the variable whose distribution
                      we want to compute)
           EvidenceVars---a LIST of Variable objects. Each of these
                          variables has had its evidence set to a particular
                          value from its domain using set_evidence.
     VE returns a distribution over the values of QueryVar, i.e., a list
     of numbers, one for every value in QueryVar's domain. These numbers
     sum to one, and the i'th number is the probability that QueryVar is
     equal to its i'th value given the setting of the evidence
     variables. For example if QueryVar = A with Dom[A] = ['a', 'b',
     'c'], EvidenceVars = [B, C], and we have previously called
     B.set_evidence(1) and C.set_evidence('c'), then VE would return a
     list of three numbers. E.g. [0.5, 0.24, 0.26]. These numbers would
     mean that Pr(A='a'|B=1, C='c') = 0.5 Pr(A='a'|B=1, C='c') = 0.24
     Pr(A='a'|B=1, C='c') = 0.26
     @return a list of probabilities, one for each item in the domain of the QueryVar
     """
    ### YOUR CODE HERE ###
    # step 1
    restrict_f = []
    for factor in Net.Factors:
        new_factor = factor
        restrict_f.append(factor)
        scope = factor.get_scope()
        for evidence_var in EvidenceVars:
            if evidence_var in scope:
                new_factor = restrict_factor(factor, evidence_var, evidence_var.get_evidence())
        restrict_f[Net.Factors.index(factor)] = new_factor
    # step 2
    ordering = min_fill_ordering(restrict_f, QueryVar)
    # print(restrict_f, QueryVar, ordering)
    for order in ordering:
        lst = []
        for factor in restrict_f:
            if order in factor.get_scope():
                lst.append(factor)
        for item in lst:
            if item in restrict_f:
                restrict_f.remove(item)
        new_multiply_factor = multiply_factors(lst)
        summation = sum_out_variable(new_multiply_factor, order)
        restrict_f.append(summation)
    # step 3
    final = []
    for value in QueryVar.domain():
        new_prob = multiply_factors(restrict_f).get_value([value])
        final.append(new_prob)

    final = normalize(final)
    return final


def NaiveBayesModel():
    '''
   NaiveBayesModel returns a BN that is a Naive Bayes model that 
   represents the joint distribution of value assignments to 
   variables in the Adult Dataset from UCI.  Remember a Naive Bayes model
   assumes P(X1, X2,.... XN, Class) can be represented as 
   P(X1|Class)*P(X2|Class)* .... *P(XN|Class)*P(Class).
   When you generated your Bayes Net, assume that the values 
   in the SALARY column of the dataset are the CLASS that we want to predict.
   @return a BN that is a Naive Bayes model and which represents the Adult Dataset. 
    '''
    ### READ IN THE DATA
    input_data = []
    with open('data/adult-dataset.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader, None)  # skip header row
        for row in reader:
            input_data.append(row)
        # print(input_data)
    ### DOMAIN INFORMATION REFLECTS ORDER OF COLUMNS IN THE DATA SET
    variable_domains = {
        "MaritalStatus": ['Not-Married', 'Married', 'Separated', 'Widowed'],
        "Relationship": ['Wife', 'Own-child', 'Husband', 'Not-in-family', 'Other-relative', 'Unmarried'],
        "Race": ['White', 'Black', 'Asian-Pac-Islander', 'Amer-Indian-Eskimo', 'Other'],
        "Gender": ['Male', 'Female'],
        "Occupation": ['Admin', 'Military', 'Manual Labour', 'Office Labour', 'Service', 'Professional'],
        "Country": ['North-America', 'South-America', 'Europe', 'Asia', 'Middle-East', 'Carribean'],
        "Education": ['<Gr12', 'HS-Graduate', 'Associate', 'Professional', 'Bachelors', 'Masters', 'Doctorate'],
        "Work": ['Not Working', 'Government', 'Private', 'Self-emp'],
        "Salary": ['<50K', '>=50K']
    }
    ### YOUR CODE HERE ###
    salary = Variable("Salary", ['<50K', '>=50K'])
    new_factor = Factor("P(salary)", [salary])
    below_50k = 0
    above_50k = 0
    total = len(input_data)
    for data in input_data:
        if '<50K' in data:
            below_50k += 1
        elif '>=50K' in data:
            above_50k += 1
    values = [['<50K', below_50k / total], ['>=50K', above_50k / total]]
    new_factor.add_values(values)
    variable_lst = []
    factor_lst = []
    adult_bn = adultDatasetBN()
    for v in adult_bn.Variables:
        if v.name != "Salary":
            factor = Factor('P(' + v.name + "|" + salary.name + ")", [v, salary])
            factor_lst.append(factor)
            variable_lst.append(v)
    variable_lst.append(salary)
    factor_lst.append(Factor('P(' + salary.name + ")", [salary]))
    naive_bn = BN("naive", variable_lst, factor_lst)

    return naive_bn


def explore(Net, question):
    '''    Input: Net---a BN object (a Bayes Net)
           question---an integer indicating the question in HW4 to be calculated. Options are:
           1. What percentage of the women in the data set end up with a P(S=">=$50K"|E1) that is strictly greater than P(S=">=$50K"|E2)?
           2. What percentage of the men in the data set end up with a P(S=">=$50K"|E1) that is strictly greater than P(S=">=$50K"|E2)?
           3. What percentage of the women in the data set with P(S=">=$50K"|E1) > 0.5 actually have a salary over $50K?
           4. What percentage of the men in the data set with P(S=">=$50K"|E1) > 0.5 actually have a salary over $50K?
           5. What percentage of the women in the data set are assigned a P(Salary=">=$50K"|E1) > 0.5, overall?
           6. What percentage of the men in the data set are assigned a P(Salary=">=$50K"|E1) > 0.5, overall?
           @return a percentage (between 0 and 100)
    '''
    ### YOUR CODE HERE ###
    salary = None
    Net = NaiveBayesModel()
    E1 = set()
    E2 = set()
    for v in Net.Variables:
        if v.name in ['Work', 'Occupation', 'Education', 'Relationship']:
            for value in v.dom:
                # print(value)
                E1.add(value)
        if v.name in ['Work', 'Occupation', 'Education', 'Relationship', 'Gender']:
            for value in v.dom:
                E2.add(value)
        if v.name == "Salary":
            salary = v

    # result = VE(Net, salary, [E1, E2])

    if question == 1:
        return 0.0
    if question == 2:
        return 0.0
    if question == 3:
        return 0.0
    if question == 4:
        return 0.0
    if question == 5:
        return 0.0
    if question == 6:
        return 0.0
