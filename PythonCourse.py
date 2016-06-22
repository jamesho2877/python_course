import pymysql
import os
import psycopg2
import urlparse
from flask import Flask, render_template, request, jsonify, json
from pymysql.err import MySQLError

app = Flask(__name__, static_url_path='', static_folder='static')


def get_connection():
    """ Connects to database
    :return: a connection
    """

    try:
        '''conn = pymysql.connect(host='localhost',
                               user='',
                               password='',
                               db='PythonCourseDB',
                               charset='utf8mb4',
                               cursorclass=pymysql.cursors.DictCursor)
        '''
        urlparse.uses_netloc.append("postgres")
        url = urlparse.urlparse(os.environ["postgres://pvgimronnimcwf:hGKQp7e53ZNrAiLVsXGNLZzIzZ@ec2-54-247-185-241.eu-west-1.compute.amazonaws.com:5432/dae2k2fpmpm4ht"])

        conn = psycopg2.connect(
            database=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        return conn

    except Exception as e:
        return json.dumps({'error': 'Connection error !'})


def query(sql_statement):
    """ Querying a statement
    :param sql_statement: a SQL statement
    :return: a list of items
    """

    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql_statement)
            conn.commit()
            entries = cursor.fetchall()
            conn.close()
            return entries

    except Exception as e:
        return json.dumps({'error': 'Querying error !'})


def get_html_list(result, _type):
    """ Mapping result into html elements
    :param result: the result from statement being queried
    :param _type: the name of object to be mapped eg. 'product' or 'customer'
    :return: html elements in json format
    """

    html = ''
    if _type == 'product':
        if len(result) > 0:
            for item in result:
                html += '<tr class="data-generated">'
                html += '<td>' + str(item.get('id')) + '</td>'
                html += '<td>' + item.get('name') + '</td>'
                html += '<td>' + str(item.get('unit_price')) + '</td>'
                html += '<td>' + str(item.get('amount')) + '</td>'
                html += "<td><button class='btnUpdate' name='" + str(item.get('id')) + "'><img src='images/update.png' alt='Update'></button>"
                html += "<button class='btnDelete' name='" + str(item.get('id')) + "'><img src='images/delete.png' alt='Delete'></button></td>"
                html += '</tr>'
        else:
            html += '<tr class="data-generated"><td class="no-data" colspan="4">No entry found !</td></tr>'

    elif _type == 'customer':
        if len(result) > 0:
            for item in result:
                html += '<tr class="data-generated">'
                html += '<td>' + str(item.get('id')) + '</td>'
                html += '<td>' + item.get('name') + '</td>'
                html += '<td>' + item.get('address') + '</td>'
                html += '<td>' + item.get('phone') + '</td>'
                html += "<td><button class='btnUpdate' name='" + str(item.get('id')) + "'><img src='images/update.png' alt='Update'></button>"
                html += "<button class='btnDelete' name='" + str(item.get('id')) + "'><img src='images/delete.png' alt='Delete'></button></td>"
                html += '</tr>'
        else:
            html += '<tr class="data-generated"><td class="no-data" colspan="4">No entry found !</td></tr>'

    else:
        if len(result) > 0:
            for item in result:
                html += '<tr class="data-generated">'
                html += '<td>' + str(item.get('customer_id')) + '</td>'
                html += '<td>' + str(item.get('product_id')) + '</td>'
                html += '<td>' + item.get('date').strftime('%d/%m/%Y') + '</td>'
                html += '<td>' + str(item.get('product_amount')) + '</td>'
                html += "<td><button class='btnUpdate' name='" + str(item.get('customer_id')) + "-" + str(item.get('product_id')) + "'><img src='images/update.png' alt='Update'></button>"
                html += "<button class='btnDelete' name='" + str(item.get('customer_id')) + "-" + str(item.get('product_id')) + "'><img src='images/delete.png' alt='Delete'></button></td>"
                html += '</tr>'
        else:
            html += '<tr class="data-generated"><td class="no-data" colspan="4">No entry found !</td></tr>'

    return json.dumps({'msg': html})


@app.route('/search_list', methods=['POST'])
def search_list():
    """ Search for specific string.
    Noted: Below params are required as an API
    :param search_string: Input of user for piece of info related to data
    :param search_field: The field that user would like to find with specific info above
    :param search_name: Name of data object to be searched
    :return: html elements in json format. If failure, return error message
    """

    text = request.form['search_string']
    field = request.form['search_field']  # const
    table = request.form['search_name']  # const

    print('search')

    try:
        if len(field) > 0 and len(table) > 0:
            my_field = 'id, name, unit_price, amount' if table == 'product' else 'id, name, address, phone' if table == 'customer' else 'customer_id, product_id, `date`, product_amount'

            additional_query = ''
            if table == 'order':
                additional_query = ' ORDER BY `date`'

            if len(text.strip()) == 0:
                result = query("SELECT " + my_field + " FROM `" + table + "`" + additional_query)
            else:
                if field == 'date':
                    text = text[-4:] + '-' + text[3:5] + '-' + text[0:2]
                    result = query("SELECT " + my_field + " FROM `" + table + "` WHERE `" + field + "` = `" + text + "`" + additional_query)

                elif field == 'name' or field == 'address' or field == 'phone':
                    result = query("SELECT " + my_field + " FROM `" + table + "` WHERE `" + field + "` LIKE '%" + text + "%'")

                else:
                    # try a different way of vision
                    result = query("SELECT {} FROM `{}` WHERE `{}` = {}{}".format(my_field, table, field, text, additional_query))

            return get_html_list(result, table)

        return json.dumps({'error': 'Error !'})

    except Exception as e:
        return json.dumps({'error': 'Error !'})


@app.route('/')
@app.route('/product', methods=['GET', 'POST'])
def product():
    """ Product object that handle adding, editing, deleting and searching for products.
    :return: different kind of information. Adding returns html elements in json format, Editing and Deleting returns
    message, Searching renders to template file with different variables. Otherwise, returns error message.
    """

    act = 'view'
    if request.method == 'POST':
        act = request.form['act']

    print(act)

    if act == 'add':
        ''' Noted: Below params are required as an API
        :param name: Name of product to be added
        :param unit_price: Unit price of product to be added
        :param amount: Amount of product to be added
        '''

        _name = request.form['name']
        _unit_price = request.form['unit_price']
        _amount = request.form['amount']

        query("INSERT INTO product (name, unit_price, amount) VALUES ('{}', {}, {})".format(_name, _unit_price,_amount))
        result = query("SELECT id, name, unit_price, amount FROM product ORDER BY id DESC LIMIT 1")

        return get_html_list(result, 'product')

    elif act == 'edit':
        ''' Noted: Below params are required as an API
        :param id: ID of product to be edited
        :param name: Name of product to be edited
        :param unit_price: Unit price of product to be edited
        :param amount: Amount of product to be edited
        '''

        _id = request.form['id']
        _name = request.form['name']
        _unit_price = request.form['unit_price']
        _amount = request.form['amount']

        try:
            query("UPDATE product SET name='{}', unit_price={}, amount={} WHERE id={}".format(_name, _unit_price, _amount, _id))
            return json.dumps({'msg': 'Saved !'})

        except Exception as e:
            return json.dumps({'error': 'Error !'})

    elif act == 'delete':
        ''' Noted: Below params are required as an API
        :param id: ID of product to be deleted
        '''

        _id = request.form['id']

        try:
            query("DELETE FROM product WHERE id='{}'".format(_id))
            return json.dumps({'msg': 'Deleted !'})

        except Exception as e:
            return json.dumps({'error': 'Error !'})

    else:
        ''' Default - Initial display for products '''

        result = query('SELECT * FROM product')
        search_field = '<option value="id">ID</option>' \
                       '<option value="name">Name</option>' \
                       '<option value="unit_price">Unit Price</option>' \
                       '<option value="amount">Amount</option>'
        column_name = '<th>ID</th><th>Name</th><th>Unit Price</th><th>Amount</th><th></th>'

        return render_template('template.html', title='Product', search_field=search_field, column_name=column_name, list=result)


@app.route('/customer', methods=['GET', 'POST'])
def customer():
    """ Customer object that handle adding, editing, deleting and searching for customers.
    :return: different kind of information. Adding returns html elements in json format, Editing and Deleting returns
    message, Searching renders to template file with different variables. Otherwise, returns error message.
    """

    act = 'view'
    if request.method == 'POST':
        act = request.form['act']

    print(act)

    if act == 'add':
        ''' Noted: Below params are required as an API
        :param name: Name of customer to be added
        :param address: Address of customer to be added
        :param phone: Phone of customer to be added
        '''

        _name = request.form['name']
        _address = request.form['address']
        _phone = request.form['phone']

        query("INSERT INTO customer (name, address, phone) VALUES ('{}', '{}', '{}')".format(_name, _address, _phone))
        result = query("SELECT id, name, address, phone FROM customer ORDER BY id DESC LIMIT 1")

        return get_html_list(result, 'customer')

    elif act == 'edit':
        ''' Noted: Below params are required as an API
        :param id: ID of customer to be edited
        :param name: Name of customer to be edited
        :param address: Address of customer to be edited
        :param phone: Phone of customer to be edited
        '''

        _id = request.form['id']
        _name = request.form['name']
        _address = request.form['address']
        _phone = request.form['phone']

        try:
            query("UPDATE customer SET name='{}', address='{}', phone='{}' WHERE id={}".format(_name, _address, _phone, _id))
            return json.dumps({'msg': 'Saved !'})

        except Exception as e:
            return json.dumps({'error': 'Error !'})

    elif act == 'delete':
        ''' Noted: Below params are required as an API
        :param id: ID of customer to be deleted
        '''

        _id = request.form['id']

        try:
            query("DELETE FROM customer WHERE id='{}'".format(_id))
            return json.dumps({'msg': 'Deleted !'})

        except Exception as e:
            return json.dumps({'error': 'Error !'})

    else:
        ''' Default - Initial display for customers '''

        result = query('SELECT * FROM customer')
        search_field = '<option value="id">ID</option>' \
                       '<option value="name">Name</option>' \
                       '<option value="address">Address</option>' \
                       '<option value="phone">Phone</option>'
        column_name = '<th>ID</th><th>Name</th><th>Address</th><th>Phone</th><th></th>'

        return render_template('template.html', title='Customer', search_field=search_field, column_name=column_name, list=result)


@app.route('/order', methods=['GET', 'POST'])
def order():
    """ Order object that handle adding, editing, deleting and searching for orders.
    :return: different kind of information. Adding returns html elements in json format, Editing and Deleting returns
    message, Searching renders to template file with different variables. Otherwise, returns error message.
    """

    act = 'view'
    if request.method == 'POST':
        act = request.form['act']

    print(act)

    if act == 'add':
        ''' Noted: Below params are required as an API
        :param cusID: Customer ID that placed order
        :param proID: Product ID that chosen by customer
        :param date: Date of order to be made
        '''

        _cusID = request.form['cusID']
        _proID = request.form['proID']
        _date = request.form['date']
        _product_amount = request.form['product_amount']

        try:
            query("INSERT INTO `order` (customer_id, product_id, `date`, product_amount) VALUES ({}, {}, '{}', {})".format(_cusID, _proID, _date, _product_amount))
            result = query("SELECT customer_id, product_id, `date`, product_amount FROM `order` WHERE customer_id=" + _cusID + " AND product_id=" + _proID)
            return get_html_list(result, 'order')

        except MySQLError as e:
            return json.dumps({'error': 'This record is existed !'})

    elif act == 'edit':
        ''' Noted: Below params are required as an API
        :param id: Pair ID which comes in form 'customer_id-product_id' of order to be edited
        :param date: Date of order to be edited
        :param product_amount: Product amount of product to be edited
        '''

        _id = request.form['id'].split('-')
        _date = request.form['date']
        _product_amount = request.form['product_amount']

        try:
            query("UPDATE `order` SET `date`='{}', product_amount={} WHERE customer_id={} AND product_id={}".format(_date, _product_amount, _id[0], _id[1]))
            return json.dumps({'msg': 'Saved !'})

        except Exception as e:
            return json.dumps({'error': 'Error !'})

    elif act == 'delete':
        ''' Noted: Below params are required as an API
            :param id: Pair ID which comes in form 'customer_id-product_id' of order to be deleted
            '''

        _id = request.form['id'].split('-')

        try:
            query("DELETE FROM `order` WHERE customer_id='{}' AND product_id={}".format(_id[0], _id[1]))
            return json.dumps({'msg': 'Deleted !'})

        except Exception as e:
            return json.dumps({'error': 'Error !'})

    else:
        ''' Default - Initial display for orders '''

        result = query("SELECT * FROM `order` ORDER BY `date`")
        search_field = '<option value="customer_id">Customer ID</option>' \
                       '<option value="product_id">Product ID</option>' \
                       '<option value="date">Date</option>' \
                       '<option value="product_amount">Product Amount</option>'
        column_name = '<th>Customer ID</th><th>Product ID</th><th>Date</th><th>Product Amount</th><th></th>'
        list1 = query("SELECT id FROM `customer`")
        list2 = query("SELECT id FROM `product`")

        opt1 = ''
        opt2 = ''
        for row in list1:
            opt1 += '<option value="' + str(row.get('id')) + '">' + str(row.get('id')) + '</option>'
        for row in list2:
            opt2 += '<option value="' + str(row.get('id')) + '">' + str(row.get('id')) + '</option>'

        return render_template('template.html', title='Order', search_field=search_field, column_name=column_name, list=result, opt1=opt1, opt2=opt2)


if __name__ == '__main__':
    app.run(debug=True)
