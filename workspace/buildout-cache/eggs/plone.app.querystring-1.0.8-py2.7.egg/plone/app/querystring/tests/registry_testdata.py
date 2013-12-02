parsed_correct = {'plone': {'app': {'querystring': {'field': {'getId': {'operations': ['plone.app.querystring.operation.string.is'], 'group': u'Metadata', 'description': u'The short name of an item (used in the url)', 'vocabulary': None, 'title': u'Short Name', 'enabled': True, 'sortable': True}, 'created': {'operations': ['plone.app.querystring.operation.date.lessThan', 'plone.app.querystring.operation.date.largerThan'], 'group': u'Dates', 'description': u'The time and date an item was created', 'vocabulary': None, 'title': u'Creation Date', 'enabled': True, 'sortable': False}}, 'operation': {'date': {'largerThan': {'widget': None, 'operation': u'plone.app.querystring.queryparser:_largerThan', 'description': u'Please use YYYY/MM/DD.', 'title': u'after'}, 'lessThan': {'widget': None, 'operation': u'plone.app.querystring.queryparser:_lessThan', 'description': u'Please use YYYY/MM/DD.', 'title': u'before'}}, 'string': {'is': {'widget': None, 'operation': u'plone.app.querystring.queryparser:_equal', 'description': u'Tip: you can use * to autocomplete.', 'title': u'equals'}}}}}}}

minimal_correct_xml = """
<registry>
    <records interface="plone.app.querystring.interfaces.IQueryOperation"
             prefix="plone.app.querystring.operation.string.is">
        <value key="title">equals</value>
        <value key="description">Tip: you can use * to autocomplete.</value>
        <value key="operation">plone.app.querystring.queryparser:_equal</value>
        <value key="widget"></value>
    </records>

    <records interface="plone.app.querystring.interfaces.IQueryOperation"
             prefix="plone.app.querystring.operation.date.lessThan">
        <value key="title">before</value>
        <value key="description">Please use YYYY/MM/DD.</value>
        <value key="operation">plone.app.querystring.queryparser:_lessThan</value>
        <value key="widget"></value>
    </records>

    <records interface="plone.app.querystring.interfaces.IQueryOperation"
             prefix="plone.app.querystring.operation.date.largerThan">
        <value key="title">after</value>
        <value key="description">Please use YYYY/MM/DD.</value>
        <value key="operation">plone.app.querystring.queryparser:_largerThan</value>
        <value key="widget"></value>
    </records>

    <records interface="plone.app.querystring.interfaces.IQueryField"
             prefix="plone.app.querystring.field.getId">
       <value key="title">Short Name</value>
       <value key="description">The short name of an item (used in the url)</value>
       <value key="enabled">True</value>
       <value key="sortable">True</value>
       <value key="operations">
            <element>plone.app.querystring.operation.string.is</element>
       </value>
       <value key="group">Metadata</value>
    </records>

    <records interface="plone.app.querystring.interfaces.IQueryField"
             prefix="plone.app.querystring.field.created">
       <value key="title">Creation Date</value>
       <value key="description">The time and date an item was created</value>
       <value key="enabled">True</value>
       <value key="sortable">False</value>
       <value key="operations">
           <element>plone.app.querystring.operation.date.lessThan</element>
           <element>plone.app.querystring.operation.date.largerThan</element>
       </value>
       <value key="group">Dates</value>
    </records>
</registry>
"""

test_missing_operator_xml = """
<registry>
    <records interface="plone.app.querystring.interfaces.IQueryOperation"
             prefix="plone.app.querystring.operation.date.lessThan">
        <value key="title">before</value>
        <value key="description">Please use YYYY/MM/DD.</value>
        <value key="operation">plone.app.querystring.queryparser:_lessThan</value>
        <value key="widget"></value>
    </records>

    <records interface="plone.app.querystring.interfaces.IQueryField"
             prefix="plone.app.querystring.field.created">
       <value key="title">Creation Date</value>
       <value key="description">The time and date an item was created</value>
       <value key="enabled">True</value>
       <value key="sortable">False</value>
       <value key="operations">
           <element>plone.app.querystring.operation.date.lessThan</element>
           <element>plone.app.querystring.operation.date.largerThan</element>
       </value>
       <value key="group">Dates</value>
    </records>
</registry>
"""

test_vocabulary_xml = """
<registry>
    <records interface="plone.app.querystring.interfaces.IQueryOperation"
             prefix="plone.app.querystring.operation.string.is">
        <value key="title">equals</value>
        <value key="description">Tip: you can use * to autocomplete.</value>
        <value key="operation">plone.app.querystring.queryparser:_equal</value>
        <value key="widget"></value>
    </records>

    <records interface="plone.app.querystring.interfaces.IQueryField"
             prefix="plone.app.querystring.field.reviewState">
        <value key="title">Review state</value>
        <value key="description">An item's workflow state (e.g.published)</value>
        <value key="enabled">True</value>
        <value key="sortable">True</value>
        <value key="operations">
            <element>plone.app.querystring.operation.string.is</element>
        </value>
        <value key="vocabulary">plone.app.querystring.tests.testvocabulary</value>
       <value key="group">Metadata</value>
    </records>
</registry>
"""
