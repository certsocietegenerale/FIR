#!/usr/bin/env python
import pyparsing as pp
import operator as op
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

## Inspired by:
# https://github.com/pyparsing/pyparsing/blob/master/examples/lucene_grammar.py
# https://danlamanna.com/posts/building-search-dsls-with-django/
# https://stackoverflow.com/questions/69191567/drf-dynamic-filtering


class BaseBinary:
    def __init__(self, tokens):
        self.args = tokens[0][0::2]

    def __repr__(self):
        return f"{self.__class__.__name__}({self.symbol}):{self.args}"

    def evaluate(self):
        a = (
            self.args[0].evaluate()
            if isinstance(self.args[0], BaseBinary)
            else self.args[0]
        )
        for item in self.args[1:]:
            item = item.evaluate() if isinstance(item, BaseBinary) else item
            a = self.op(a, item)
        return a


class BoolNotOp(BaseBinary):
    symbol = "NOT"
    op = op.not_

    def __init__(self, tokens):
        super().__init__(tokens)
        self.args = tokens[0][1]

    def evaluate(self):
        a = self.args.evaluate() if isinstance(self.args, BaseBinary) else self.args
        return ~a


class BoolAndOp(BaseBinary):
    symbol = "AND"
    op = op.and_


class BoolOrOp(BaseBinary):
    symbol = "OR"
    op = op.or_


class SearchParser:
    def __init__(self, valid_fields, default_fields, search_query):
        self.valid_fields = valid_fields
        self.default_fields = default_fields
        self.query = search_query

        q = self.get_search_grammar().parse_string(search_query)[0]

        if isinstance(q, Q):
            self.q = q
        else:
            self.q = q.evaluate()

    def field_to_q(self, t):
        if "field" in t:
            if t[0].lower() in self.valid_fields.keys():
                current_field = self.valid_fields[t[0].lower()]
                if callable(current_field):
                    return current_field(t[2])
                else:
                    return Q(**{current_field: t[2]})
            else:
                raise Exception(
                    _(
                        f"Field '%s' does not exist. Valid fields are: %s."
                        % (t[0], ", ".join(self.valid_fields.keys()))
                    )
                )
        elif isinstance(t[0], str):
            # Text entered without "field:"
            ret = Q()
            for x in self.default_fields:
                ret |= x(t[0])
            return ret
        else:
            # brackets. Default logical operator: and
            ret = Q()
            for x in t:
                ret &= x
            return ret

    def get_q(self):
        return self.q

    def get_search_grammar(self):
        pp.ParserElement.enable_packrat()

        COLON, LBRACK, RBRACK, LBRACE, RBRACE = pp.Literal.using_each(":[]{}")
        LPAR, RPAR = pp.Suppress.using_each("()")
        and_, or_, not_ = pp.CaselessKeyword.using_each("&& || !".split())

        expression = pp.Forward()

        valid_word = pp.Regex(
            r'([\w_.-]|\\\\|\\([+\-!(){}\[\]^"~*?:]|\|\||&&))'
            r'([\w*_+.-]|\\\\|\\([+\-!(){}\[\]^"~*?:]|\|\||&&)|\*|\?)*'
        ).setName("word")
        valid_word.set_parse_action(
            lambda t: t[0]
            .replace("\\\\", chr(127))
            .replace("\\", "")
            .replace(chr(127), "\\")
        )

        string = pp.QuotedString('"')

        term = pp.Forward().set_name("term")
        field_name = valid_word().set_name("fieldname")

        term <<= pp.Opt(field_name("field") + COLON).set_name("field") + (
            valid_word | string | pp.Group(LPAR + expression + RPAR)
        )
        term.set_parse_action(self.field_to_q)

        expression <<= pp.infix_notation(
            term,
            [
                (not_.set_parse_action(lambda: "NOT"), 1, pp.OpAssoc.RIGHT, BoolNotOp),
                (or_.set_parse_action(lambda: "OR"), 2, pp.OpAssoc.LEFT, BoolOrOp),
                (
                    pp.Opt(and_).setName("and").set_parse_action(lambda: "AND"),
                    2,
                    pp.OpAssoc.LEFT,
                    BoolAndOp,
                ),
            ],
        )
        return expression
