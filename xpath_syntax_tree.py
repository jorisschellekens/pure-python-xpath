import re

from xpath_tokenizer import XPATHTokenizer


class Expression:
    """
    This class represents the base of all expressions in an xpath syntax tree.
    """

    def __init__(self):
        self.token = ''
        self.children = []
        self.parent = None

    def add_child(self, n):
        """
        This method adds a child node to this Expression
        :param n:   the child to be added
        :return:    self
        """
        n.parent = self
        self.children.append(n)
        return self

    def evaluate(self, node_set_pos, node_set_neg):
        """
        This method evaluates the current Expression
        :param node_set_pos:    the nodes that were previously selected (the operating set of this Expression)
        :param node_set_neg:    the nodes that were previously rejected (useful for negation operator)
        :return:                a tuple (selected, rejected) nodes
        """
        pass

#
# literals
#

class AttributeName(Expression):
    """
    This class represents an attribute name. These begin with '@'
    """

    def __init__(self, txt):
        super().__init__()
        self.value = txt[1:]

class StringLiteral(Expression):
    """
    This class represents a string literal. These are encased by single quotation marks.
    """

    def __init__(self, txt):
        super().__init__()
        self.value = txt[1:len(txt)-1]

class NumberLiteral(Expression):
    """
    This class represents a number.
    """

    def __init__(self, txt):
        super().__init__()
        self.value = int(txt)

#
# XPath uses path expressions to select nodes in an XML document.
# The node is selected by following a path or steps.
# The most useful path expressions are listed below:
#

class SelectFromRootNode(Expression):
    """
    This class handles the '/' token of an XPATH expression
    """

    def __init__(self):
        super().__init__()

    def evaluate(self, node_set_pos, node_set_neg):
        return (node_set_pos, node_set_neg)

class SelectAll(Expression):
    """
    This class handles the '//' token of an XPATH expression
    """

    def __init__(self):
        super().__init__()

    def evaluate(self, node_set_pos, node_set_neg):
        o = []
        for x in node_set_pos:
            for y in x.find_all():
                o.append(y)
        return (o, [])

class SelectStar(SelectAll):
    """
    This class handles the '*' token of an XPATH expression
    """

    def __init__(self):
        super().__init__()

    def evaluate(self, node_set_pos, node_set_neg):
        return super().evaluate(node_set_pos, node_set_neg)

class SelectHTMLTag(Expression):
    """
    This class handles any HTML-tag token of an XPATH expression
    """

    def __init__(self, tag_name):
        super().__init__()
        self.tag_name = tag_name

    def evaluate(self, node_set_pos, node_set_neg):
        return ([x for x in node_set_pos if x.name == self.tag_name], [])

class SelectText(Expression):
    """
    This class handles the 'text()' token of an XPATH expression
    """

    def __init__(self):
        super().__init__()

    def evaluate(self, node_set_pos, node_set_neg):
        return [x.text for x in node_set_pos]

class SelectAttribute(Expression):
    """
    This class handles the '@attr' token of an XPATH expression
    when it is not part of a predicate.
    """
    def __init__(self, attribute_name):
        super().__init__()
        self.attribute_name =  attribute_name[1:]

    def evaluate(self, node_set_pos, node_set_neg):
        return [(x.attrs[self.attribute_name] if self.attribute_name in x.attrs else '') for x in node_set_pos]

#
# Predicates are used to find a specific node or a node that contains a specific value.
# Predicates are always embedded in square brackets.
#

class Predicate(Expression):

    def __init__(self):
        super().__init__()

class Comparison(Predicate):
    """
    This is a common base class for comparison operators in the XPATH language
    """

    def __init__(self):
        super().__init__()

    def _check_arguments(self):

        r = self.children[0]
        l = self.children[1]

        # exceptions
        if l.__class__.__name__ not in ['AttributeName', 'NumberLiteral', 'StringLiteral']:
            raise SyntaxError('Invalid arguments for comparison operator in XPATH')
        if r.__class__.__name__ not in ['AttributeName', 'NumberLiteral', 'StringLiteral']:
            raise SyntaxError('Invalid arguments for comparison operator in XPATH')
        if l.__class__.__name__  == 'NumberLiteral' and r.__class__.__name__  == 'StringLiteral':
            raise SyntaxError('Mismatched operands for comparison in XPATH. Can not compare str and float.')
        if l.__class__.__name__  == 'StringLiteral' and r.__class__.__name__  == 'NumberLiteral':
            raise SyntaxError('Mismatched operands for comparison in XPATH. Can not compare str and float.')


class GreaterThan(Comparison):
    """
    This class implements the 'greater than' operator
    """

    def __init__(self):
        super().__init__()

    def evaluate(self, node_set_pos, node_set_neg):

        super()._check_arguments()

        # literal arguments only
        r = self.children[0]
        l = self.children[1]
        if l.__class__.__name__ != 'AttributeName' and l.__class__.__name__ != 'AttributeName':
            if l.value > r.value:
                return (node_set_pos, node_set_neg)
            else:
                return ([], node_set_pos)

        # both arguments are an attribute name
        if l.__class__.__name__ == r.__class__.__name__ == 'AttributeName':
            pos = [x for x in node_set_pos if (l.value in x.attrs and r.value in x.attrs and x.attrs[l.value] > x.attrs[r.value])]
            neg = [x for x in node_set_pos if x not in pos]
            return (pos, neg)

        # one of the arguments is an attribute name
        if l.__class__.__name__ == 'AttributeName':
            pos = [x for x in node_set_pos if (l.value in x.attrs and x.attrs[l.value] > r.value)]
            neg = [x for x in node_set_pos if x not in pos]
            return (pos, neg)
        if r.__class__.__name__ == 'AttributeName':
            pos = [x for x in node_set_pos if (r.value in x.attrs and l.value > x.attrs[r.value])]
            neg = [x for x in node_set_pos if x not in pos]
            return (pos, neg)


class GreaterThanOrEqual(Comparison):
    """
    This class implements the 'greater than or equal' operator
    """

    def __init__(self):
        super().__init__()

    def evaluate(self, node_set_pos, node_set_neg):

        super()._check_arguments()

        # literal arguments only
        r = self.children[0]
        l = self.children[1]
        if l.__class__.__name__ != 'AttributeName' and l.__class__.__name__ != 'AttributeName':
            if l.value >= r.value:
                return (node_set_pos, node_set_neg)
            else:
                return ([], node_set_pos)

        # both arguments are an attribute name
        if l.__class__.__name__ == r.__class__.__name__ == 'AttributeName':
            pos = [x for x in node_set_pos if (l.value in x.attrs and r.value in x.attrs and x.attrs[l.value] >= x.attrs[r.value])]
            neg = [x for x in node_set_pos if x not in pos]
            return (pos, neg)

        # one of the arguments is an attribute name
        if l.__class__.__name__ == 'AttributeName':
            pos = [x for x in node_set_pos if (l.value in x.attrs and x.attrs[l.value] >= r.value)]
            neg = [x for x in node_set_pos if x not in pos]
            return (pos, neg)
        if r.__class__.__name__ == 'AttributeName':
            pos = [x for x in node_set_pos if (r.value in x.attrs and l.value >= x.attrs[r.value])]
            neg = [x for x in node_set_pos if x not in pos]
            return (pos, neg)


class SmallerThan(Comparison):
    """
    This class implements the 'smaller than' operator
    """

    def __init__(self):
        super().__init__()

    def evaluate(self, node_set_pos, node_set_neg):

        super()._check_arguments()

        # literal arguments only
        r = self.children[0]
        l = self.children[1]
        if l.__class__.__name__ != 'AttributeName' and l.__class__.__name__ != 'AttributeName':
            if l.value < r.value:
                return (node_set_pos, node_set_neg)
            else:
                return ([], node_set_pos)

        # both arguments are an attribute name
        if l.__class__.__name__ == r.__class__.__name__ == 'AttributeName':
            pos = [x for x in node_set_pos if (l.value in x.attrs and r.value in x.attrs and x.attrs[l.value] < x.attrs[r.value])]
            neg = [x for x in node_set_pos if x not in pos]
            return (pos, neg)

        # one of the arguments is an attribute name
        if l.__class__.__name__ == 'AttributeName':
            pos = [x for x in node_set_pos if (l.value in x.attrs and x.attrs[l.value] < r.value)]
            neg = [x for x in node_set_pos if x not in pos]
            return (pos, neg)
        if r.__class__.__name__ == 'AttributeName':
            pos = [x for x in node_set_pos if (r.value in x.attrs and l.value < x.attrs[r.value])]
            neg = [x for x in node_set_pos if x not in pos]
            return (pos, neg)


class SmallerThanOrEqual(Comparison):
    """
    This class implements the 'smaller than or equal' operator
    """

    def __init__(self):
        super().__init__()

    def evaluate(self, node_set_pos, node_set_neg):

        super()._check_arguments()

        # literal arguments only
        r = self.children[0]
        l = self.children[1]
        if l.__class__.__name__ != 'AttributeName' and l.__class__.__name__ != 'AttributeName':
            if l.value <= r.value:
                return (node_set_pos, node_set_neg)
            else:
                return ([], node_set_pos)

        # both arguments are an attribute name
        if l.__class__.__name__ == r.__class__.__name__ == 'AttributeName':
            pos = [x for x in node_set_pos if (l.value in x.attrs and r.value in x.attrs and x.attrs[l.value] <= x.attrs[r.value])]
            neg = [x for x in node_set_pos if x not in pos]
            return (pos, neg)

        # one of the arguments is an attribute name
        if l.__class__.__name__ == 'AttributeName':
            pos = [x for x in node_set_pos if (l.value in x.attrs and x.attrs[l.value] <= r.value)]
            neg = [x for x in node_set_pos if x not in pos]
            return (pos, neg)
        if r.__class__.__name__ == 'AttributeName':
            pos = [x for x in node_set_pos if (r.value in x.attrs and l.value <= x.attrs[r.value])]
            neg = [x for x in node_set_pos if x not in pos]
            return (pos, neg)


class Equal(Comparison):
    """
    This class implements the equality operator
    """

    def __init__(self):
        super().__init__()

    def evaluate(self, node_set_pos, node_set_neg):

        super()._check_arguments()

        # literal arguments only
        r = self.children[0]
        l = self.children[1]
        if l.__class__.__name__ != 'AttributeName' and l.__class__.__name__ != 'AttributeName':
            if l.value == r.value:
                return (node_set_pos, node_set_neg)
            else:
                return ([], node_set_pos)

        # both arguments are an attribute name
        if l.__class__.__name__ == r.__class__.__name__ == 'AttributeName':
            pos = [x for x in node_set_pos if (l.value in x.attrs and r.value in x.attrs and x.attrs[l.value] == x.attrs[r.value])]
            neg = [x for x in node_set_pos if x not in pos]
            return (pos, neg)

        # one of the arguments is an attribute name
        if l.__class__.__name__ == 'AttributeName':
            pos = [x for x in node_set_pos if (l.value in x.attrs and x.attrs[l.value] == r.value)]
            neg = [x for x in node_set_pos if x not in pos]
            return (pos, neg)
        if r.__class__.__name__ == 'AttributeName':
            pos = [x for x in node_set_pos if (r.value in x.attrs and l.value == x.attrs[r.value])]
            neg = [x for x in node_set_pos if x not in pos]
            return (pos, neg)


class NotEqual(Comparison):
    """
    This class implements the inequality operator
    """

    def __init__(self):
        super().__init__()

    def evaluate(self, node_set_pos, node_set_neg):

        super()._check_arguments()

        # literal arguments only
        r = self.children[0]
        l = self.children[1]
        if l.__class__.__name__ != 'AttributeName' and l.__class__.__name__ != 'AttributeName':
            if l.value != r.value:
                return (node_set_pos, node_set_neg)
            else:
                return ([], node_set_pos)

        # both arguments are an attribute name
        if l.__class__.__name__ == r.__class__.__name__ == 'AttributeName':
            pos = [x for x in node_set_pos if (l.value in x.attrs and r.value in x.attrs and x.attrs[l.value] != x.attrs[r.value])]
            neg = [x for x in node_set_pos if x not in pos]
            return (pos, neg)

        # one of the arguments is an attribute name
        if l.__class__.__name__ == 'AttributeName':
            pos = [x for x in node_set_pos if (l.value in x.attrs and x.attrs[l.value] != r.value)]
            neg = [x for x in node_set_pos if x not in pos]
            return (pos, neg)
        if r.__class__.__name__ == 'AttributeName':
            pos = [x for x in node_set_pos if (r.value in x.attrs and l.value != x.attrs[r.value])]
            neg = [x for x in node_set_pos if x not in pos]
            return (pos, neg)

#
# logic predicates
#

class LogicalAnd(Predicate):
    """
    This class implements the 'AND' operator
    """

    def __init__(self):
        super().__init__()

    def evaluate(self, node_set_pos, node_set_neg):

        (a,b) = self.children[0].evaluate(node_set_pos, node_set_neg)
        (c,d) = self.children[0].evaluate(node_set_pos, node_set_neg)

        # return
        pos = [x for x in a if x in c]
        neg = list(set([x for x in (a+b+c+d) if x not in pos]))
        return (pos, neg)

class LogicalOr(Predicate):
    """
    This class implements the 'OR' operator
    """

    def __init__(self):
        super().__init__()

    def evaluate(self, node_set_pos, node_set_neg):

        (a, b) = self.children[0].evaluate(node_set_pos, node_set_neg)
        (c, d) = self.children[0].evaluate(node_set_pos, node_set_neg)

        # return
        pos = list(set(c) | set(a))
        neg = list(set([x for x in (a+b+c+d) if x not in pos]))
        return (pos, neg)

class LogicalNot(Predicate):
    """
    This class implements the 'NOT' operator
    """

    def __init__(self):
        super().__init__()

    def evaluate(self, node_set_pos, node_set_neg):
        return (node_set_neg, node_set_pos)

#
# text-related predicates
#

class TextContains(Predicate):

    def __init__(self):
        super().__init__()

    def evaluate(self, node_set_pos, node_set_neg):

        # nodes where an attribute is equal to a given value
        atr = None
        val = None
        if self.children[0].__class__.__name__ == 'AttributeName' and self.children[1].__class__.__name__ == 'StringLiteral':
            atr = self.children[0].value
            val = self.children[1].value
        if self.children[1].__class__.__name__ == 'AttributeName' and self.children[0].__class__.__name__ == 'StringLiteral':
            atr = self.children[1].value
            val = self.children[0].value

        # return
        pos = [x for x in node_set_pos if (atr in x.attrs and val in x.attrs[atr])]
        neg = [x for x in node_set_pos if (atr not in x.attrs or val not in x.attrs[atr])]
        return (pos, neg)

class TextStartsWith(Predicate):

    def __init__(self):
        super().__init__()

    def evaluate(self, node_set_pos, node_set_neg):

        # nodes where an attribute is equal to a given value
        atr = None
        val = None
        if self.children[0].__class__.__name__ == 'AttributeName' and self.children[1].__class__.__name__ == 'StringLiteral':
            atr = self.children[0].value
            val = self.children[1].value
        if self.children[1].__class__.__name__ == 'AttributeName' and self.children[0].__class__.__name__ == 'StringLiteral':
            atr = self.children[1].value
            val = self.children[0].value

        # return
        pos = [x for x in node_set_pos if (atr in x.attrs and x.attrs[atr].startswith(val))]
        neg = [x for x in node_set_pos if (atr not in x.attrs or not x.attrs[atr].startswith(val))]
        return (pos, neg)

class TextEndsWith(Predicate):

    def __init__(self):
        super().__init__()

    def evaluate(self, node_set_pos, node_set_neg):

        # nodes where an attribute is equal to a given value
        atr = None
        val = None
        if self.children[0].__class__.__name__ == 'AttributeName' and self.children[1].__class__.__name__ == 'StringLiteral':
            atr = self.children[0].value
            val = self.children[1].value
        if self.children[1].__class__.__name__ == 'AttributeName' and self.children[0].__class__.__name__ == 'StringLiteral':
            atr = self.children[1].value
            val = self.children[0].value

        # return
        pos = [x for x in node_set_pos if (atr in x.attrs and x.attrs[atr].endswith(val))]
        neg = [x for x in node_set_pos if (atr not in x.attrs or not x.attrs[atr].endswith(val))]
        return (pos, neg)

class TextLength(Predicate):

    def __init__(self):
        super().__init__()

    def evaluate(self, node_set_pos, node_set_neg):
        raise NotImplementedError()

class XPATHSyntaxTree:

    def xpath_to_syntax_tree(self, xpath_expression):

        # tokenize
        tokens = XPATHTokenizer().tokenize_expression(xpath_expression)

        # replace each part by its matching syntax tree
        nodes = []
        i = 0
        while i < len(tokens):

            # predicate
            if tokens[i] == '[':
                j = tokens.index(']', i)
                nodes.append(self._predicate_postfix_to_tree(self._predicate_to_postfix(tokens[i:j+1])))
                i = j + 1
                continue

            # select from root node
            if tokens[i] == '/':
                nodes.append(SelectFromRootNode())
                i += 1
                continue

            # select all
            if tokens[i] == '//':
                nodes.append(SelectAll())
                i += 1
                continue

            # select star
            if tokens[i] == '*':
                nodes.append(SelectStar())
                i += 1
                continue

            # select attribute
            if tokens[i].startswith('@'):
                nodes.append(SelectAttribute(tokens[i]))
                i += 1
                continue

            # select text
            if tokens[i] == 'text':
                nodes.append(SelectText())
                if tokens[i+1] == '(' and tokens[i+2] == ')':
                    i += 2
                i += 1
                continue

            # select HTML tag
            if re.compile('^[a-zA-Z]+$').match(tokens[i]):
                nodes.append(SelectHTMLTag(tokens[i]))
                i += 1
                continue

            # default : next iteration
            i += 1

        # return
        return nodes

    def _predicate_postfix_to_tree(self, xpath_postfix_predicate_expression):

        tree = []
        for t in xpath_postfix_predicate_expression:

            # operands
            if t.startswith('@'):
                tree.append(AttributeName(t))
                continue
            if t.startswith('\''):
                tree.append(StringLiteral(t))
                continue
            if re.compile('^[0-9]+').match(t):
                tree.append(NumberLiteral(t))
                continue

            # relationship operators
            if t == '>':
                tree.append(GreaterThan().add_child(tree.pop(-1)).add_child(tree.pop(-1)))
            if t == '>=':
                tree.append(GreaterThanOrEqual().add_child(tree.pop(-1)).add_child(tree.pop(-1)))
            if t == '<':
                tree.append(SmallerThan().add_child(tree.pop(-1)).add_child(tree.pop(-1)))
            if t == '<=':
                tree.append(SmallerThanOrEqual().add_child(tree.pop(-1)).add_child(tree.pop(-1)))
            if t == '=':
                tree.append(Equal().add_child(tree.pop(-1)).add_child(tree.pop(-1)))
            if t == '!=':
                tree.append(NotEqual().add_child(tree.pop(-1)).add_child(tree.pop(-1)))

            # logical operators
            if t == 'and':
                tree.append(LogicalAnd().add_child(tree.pop(-1)).add_child(tree.pop(-1)))
            if t == 'or':
                tree.append(LogicalOr().add_child(tree.pop(-1)).add_child(tree.pop(-1)))
            if t == 'not':
                tree.append(LogicalNot().add_child(tree.pop(-1)))

            # text operators
            if t == 'ends-with':
                tree.append(TextEndsWith().add_child(tree.pop(-1)).add_child(tree.pop(-1)))
            if t == 'starts-with':
                tree.append(TextStartsWith().add_child(tree.pop(-1)).add_child(tree.pop(-1)))
            if t == 'contains':
                tree.append(TextContains().add_child(tree.pop(-1)).add_child(tree.pop(-1)))
            if t == 'length':
                tree.append(TextLength().add_child(tree.pop(-1)))

        # return
        return tree[0]

    def _precedence(self, xpath_operator):
        if xpath_operator == '=':
            return 1
        if xpath_operator == 'or':
            return 2
        if xpath_operator == 'and':
            return 3
        if xpath_operator in ['>','>=','<','<=']:
            return 4
        if xpath_operator in ['+','-']:
            return 5
        if xpath_operator in ['mul','div']:
            return 6
        if xpath_operator == 'not':
            return 7
        # default
        return 8

    def _is_left_associative(self, xpath_operator):
        return True

    def _predicate_to_postfix(self, xpath_predicate_expression):

        # convenience array to hold brackets
        l_b = ['(','{','[']
        r_b = [')','}',']']

        # output
        out = []

        # while there are tokens to be read
        i = 0
        operator_stack = []
        while i < len(xpath_predicate_expression):

            # get current token
            t = xpath_predicate_expression[i]

            # if the token is a comma, ignore
            if t == ',':
                i += 1
                continue

            # if the token is a whitespace, ignore
            if t == ' ':
                i += 1
                continue

            # if the token is a left paren, then push it onto the operator stack.
            if t in l_b:
                operator_stack.append(t)
                i += 1
                continue

            # if the token is a right paren, then:
            # while the operator at the top of the operator stack is not a left paren:
            #   pop the operator from the operator stack onto the output queue.
            if t in r_b:
                while len(operator_stack) > 0 and operator_stack[-1] not in l_b:
                    out.append(operator_stack.pop(-1))
                if operator_stack[-1] in l_b:
                    operator_stack.pop(-1)
                i += 1
                continue

            # if the token is an operand then push it to the output queue
            is_operand = t.startswith('@') or t.startswith('\'')
            is_operator = not is_operand
            if is_operand:
                out.append(t)
                i += 1
                continue

            # if the token is an operator, then:
            #   while ((there is a function at the top of the operator stack)
            #       or (there is an operator at the top of the operator stack with greater precedence)
            #       or (the operator at the top of the operator stack has equal precedence and the token is left associative))
            #       and (the operator at the top of the operator stack is not a left parenthesis):
            #   pop operators from the operator stack onto the output queue.
            if is_operator:
                while len(operator_stack) > 0               \
                        and operator_stack[-1] not in l_b   \
                        and (
                        self._precedence(operator_stack[-1]) > self._precedence(t) \
                        or (self._precedence(operator_stack[-1]) == self._precedence(t) and self._is_left_associative(t))
                ):
                    out.append(operator_stack.pop(-1))

                #   push it onto the operator stack.
                operator_stack.append(t)
                i += 1
                continue

        # return
        return out