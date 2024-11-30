from flask import Flask, request, send_from_directory, abort, jsonify
from flasgger import Swagger, swag_from
from datetime import datetime, timezone, timedelta
import pymysql
import os
import zoneinfo

app = Flask(__name__)
swagger = Swagger(app)

# Constants and configurations
PHOTO_DIR = '/workspace/photo'
DATABASE_CONFIG = {
    'host': 'mysql',
    'port': 3306,
    'user': 'root',
    'password': 'gaeun',
    'db': 'baemin1',
    'cursorclass': pymysql.cursors.DictCursor,
}

# Helper functions
def get_db_connection():
    return pymysql.connect(**DATABASE_CONFIG)

def compute_order_status(store):
    tz_seoul = zoneinfo.ZoneInfo("Asia/Seoul")
    now = datetime.now(tz_seoul)

    start_time_str = str(store['startTime'])
    end_time_str = str(store['endTime'])

    start_time = datetime.strptime(start_time_str, '%H:%M:%S').time()
    end_time = datetime.strptime(end_time_str, '%H:%M:%S').time()

    today = now.date()
    start_datetime = datetime.combine(today, start_time, tzinfo=tz_seoul)
    end_datetime = datetime.combine(today, end_time, tzinfo=tz_seoul)

    # Handle cases where the store closes after midnight
    if end_datetime <= start_datetime:
        end_datetime += timedelta(days=1)

    if start_datetime <= now <= end_datetime:
        return None
    elif now < start_datetime:
        return f"주문 불가 - 오늘 {start_time.strftime('%H:%M')}에 오픈"
    else:
        return f"주문 불가 - 내일 {start_time.strftime('%H:%M')}에 오픈"

def get_stores(category, order_by=None, coupon_only=False):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            base_sql = """
                SELECT 
                    s.storeId, 
                    s.name AS storeName, 
                    s.category, 
                    s.address, 
                    s.storePictureUrl, 
                    s.phone, 
                    s.rating, 
                    s.reviewCount,
                    s.minDeliveryTime,
                    s.maxDeliveryTime,
                    s.minDeliveryTip,
                    s.maxDeliveryTip,
                    s.minDeliveryPrice,
                    s.startTime,
                    s.endTime,
                    IF(MAX(c.name) IS NOT NULL, "쿠폰", "") AS coupon
                FROM Stores s
                LEFT JOIN Coupons c ON s.storeId = c.storeId AND c.status = '일반'
                WHERE s.status = '일반' AND s.category = %s
            """
            if coupon_only:
                base_sql += " AND c.status = '일반' "
            base_sql += " GROUP BY s.storeId "
            if order_by:
                base_sql += f" ORDER BY {order_by} "
            params = [category]
            cursor.execute(base_sql, params)
            stores = cursor.fetchall()
            return stores
    finally:
        conn.close()

def get_menus():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            menu_sql = """
                SELECT 
                    m.storeId, m.name AS menuName, m.price AS menuPrice, m.menuPictureUrl
                FROM Menu m
                WHERE m.status = '일반'
            """
            cursor.execute(menu_sql)
            menus = cursor.fetchall()
            return menus
    finally:
        conn.close()

def merge_stores_and_menus(stores, menus):
    menus_by_store = {}
    for menu in menus:
        store_id = menu['storeId']
        menus_by_store.setdefault(store_id, []).append(menu)

    stores_result = []
    for store in stores:
        store['orderStatus'] = compute_order_status(store)
        store['startTime'] = str(store['startTime'])
        store['endTime'] = str(store['endTime'])
        store_id = store['storeId']
        store['menus'] = menus_by_store.get(store_id, [])
        stores_result.append(store)
    return stores_result

# Serve photo
@app.route('/photo/<path:filename>', methods=['GET'])
@swag_from({
    'tags': ['Photo Service'],
    'parameters': [
        {
            'name': 'filename',
            'in': 'path',
            'type': 'string',
            'required': True,
            'description': 'Filename of the photo to retrieve'
        }
    ],
    'responses': {
        200: {
            'description': 'Photo file retrieved successfully'
        },
        404: {
            'description': 'Photo not found'
        }
    }
})
def serve_photo(filename):
    """
    Serve a photo file from the server.
    ---
    """
    file_path = os.path.join(PHOTO_DIR, filename)
    if not os.path.exists(file_path):
        return abort(404)
    return send_from_directory(PHOTO_DIR, filename)

# Hello World
@app.route('/', methods=['GET'])
@swag_from({
    'tags': ['General'],
    'responses': {
        200: {
            'description': 'Greeting message'
        }
    }
})
def get_echo_call():
    """
    Returns a simple greeting message.
    ---
    """
    return 'Hello, World'

# View 2 Routes
@app.route('/samecategory', methods=['GET'])
@swag_from({
    'tags': ['Store Listings'],
    'parameters': [
        {
            'name': 'category',
            'in': 'query',
            'type': 'string',
            'required': True,
            'description': 'Category of stores to fetch'
        }
    ],
    'responses': {
        200: {
            'description': 'List of stores in the same category',
            'schema': {
                'type': 'array',
                'items': {'type': 'object'}
            }
        }
    }
})
def same_category():
    """
    Get stores in the same category
    ---
    """
    category_input = request.args.get('category')
    if not category_input:
        return jsonify({'error': 'Category parameter is required'}), 400
    stores = get_stores(category_input)
    menus = get_menus()
    stores_result = merge_stores_and_menus(stores, menus)
    return jsonify(stores_result)

@app.route('/mindeliverytime', methods=['GET'])
@swag_from({
    'tags': ['Store Listings'],
    'parameters': [
        {
            'name': 'category',
            'in': 'query',
            'type': 'string',
            'required': True,
            'description': 'Category of stores to fetch'
        }
    ],
    'responses': {
        200: {
            'description': 'List of stores sorted by minimum delivery time',
            'schema': {
                'type': 'array',
                'items': {'type': 'object'}
            }
        }
    }
})
def min_delivery_time():
    """
    Get stores sorted by minimum delivery time
    ---
    """
    category_input = request.args.get('category')
    if not category_input:
        return jsonify({'error': 'Category parameter is required'}), 400
    stores = get_stores(category_input, order_by='s.minDeliveryTime ASC')
    menus = get_menus()
    stores_result = merge_stores_and_menus(stores, menus)
    return jsonify(stores_result)

@app.route('/mindeliverytip', methods=['GET'])
@swag_from({
    'tags': ['Store Listings'],
    'parameters': [
        {
            'name': 'category',
            'in': 'query',
            'type': 'string',
            'required': True,
            'description': 'Category of stores to fetch'
        }
    ],
    'responses': {
        200: {
            'description': 'List of stores sorted by minimum delivery tip',
            'schema': {
                'type': 'array',
                'items': {'type': 'object'}
            }
        }
    }
})
def min_delivery_tip():
    """
    Get stores sorted by minimum delivery tip
    ---
    """
    category_input = request.args.get('category')
    if not category_input:
        return jsonify({'error': 'Category parameter is required'}), 400
    stores = get_stores(category_input, order_by='s.minDeliveryTip ASC')
    menus = get_menus()
    stores_result = merge_stores_and_menus(stores, menus)
    return jsonify(stores_result)

@app.route('/highestrating', methods=['GET'])
@swag_from({
    'tags': ['Store Listings'],
    'parameters': [
        {
            'name': 'category',
            'in': 'query',
            'type': 'string',
            'required': True,
            'description': 'Category of stores to fetch'
        }
    ],
    'responses': {
        200: {
            'description': 'List of stores sorted by highest rating',
            'schema': {
                'type': 'array',
                'items': {'type': 'object'}
            }
        }
    }
})
def highest_rating():
    """
    Get stores sorted by highest rating
    ---
    """
    category_input = request.args.get('category')
    if not category_input:
        return jsonify({'error': 'Category parameter is required'}), 400
    stores = get_stores(category_input, order_by='s.rating DESC')
    menus = get_menus()
    stores_result = merge_stores_and_menus(stores, menus)
    return jsonify(stores_result)

@app.route('/couponstores', methods=['GET'])
@swag_from({
    'tags': ['Store Listings'],
    'parameters': [
        {
            'name': 'category',
            'in': 'query',
            'type': 'string',
            'required': True,
            'description': 'Category of stores to fetch with coupons'
        }
    ],
    'responses': {
        200: {
            'description': 'List of stores offering coupons',
            'schema': {
                'type': 'array',
                'items': {'type': 'object'}
            }
        }
    }
})
def coupon_stores():
    """
    Get stores offering coupons
    ---
    """
    category_input = request.args.get('category')
    if not category_input:
        return jsonify({'error': 'Category parameter is required'}), 400
    stores = get_stores(category_input, coupon_only=True)
    menus = get_menus()
    stores_result = merge_stores_and_menus(stores, menus)
    return jsonify(stores_result)

# View 3 Routes
@app.route('/storeinfo', methods=['GET'])
@swag_from({
    'tags': ['Store Details'],
    'parameters': [
        {
            'name': 'storeId',
            'in': 'query',
            'type': 'integer',
            'required': True,
            'description': 'ID of the store'
        }
    ],
    'responses': {
        200: {
            'description': 'Store information',
            'schema': {'type': 'object'}
        }
    }
})
def store_info():
    """
    Get store information
    ---
    """
    store_id = request.args.get('storeId')
    if not store_id:
        return jsonify({'error': 'storeId parameter is required'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            store_info_sql = """
                SELECT 
                    s.storePictureUrl AS `storePicture`,
                    s.name AS `storeName`,
                    s.rating AS `rating`,
                    s.reviewCount AS `reviewCount`,
                    s.minDeliveryTip, 
                    s.maxDeliveryTip,
                    s.minDeliveryPrice AS `minOrderPrice`,
                    s.minDeliveryTime AS `minDeliveryTime`,
                    s.maxDeliveryTime AS `maxDeliveryTime`,
                    s.content AS `description`,
                    c.name AS `couponName`,
                    c.content AS `couponContent`
                FROM Stores s
                LEFT JOIN Coupons c ON s.storeId = c.storeId AND c.status = '일반'
                WHERE s.status = '일반' 
                AND s.storeId = %s
            """
            cursor.execute(store_info_sql, [store_id])
            store_info = cursor.fetchone()
            if store_info:
                store_info['minDeliveryTime'] = str(store_info['minDeliveryTime'])
                store_info['maxDeliveryTime'] = str(store_info['maxDeliveryTime'])
            else:
                store_info = {}
            return jsonify(store_info)
    finally:
        conn.close()

@app.route('/storedetails', methods=['GET'])
@swag_from({
    'tags': ['Store Details'],
    'parameters': [
        {
            'name': 'storeId',
            'in': 'query',
            'type': 'integer',
            'required': True,
            'description': 'ID of the store'
        }
    ],
    'responses': {
        200: {
            'description': 'Detailed store information',
            'schema': {'type': 'object'}
        }
    }
})
def store_details():
    """
    Get detailed store information
    ---
    """
    store_id = request.args.get('storeId')
    if not store_id:
        return jsonify({'error': 'storeId parameter is required'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            store_details_sql = """
                SELECT 
                    s.name AS `storeName`,
                    s.address AS `address`,
                    s.phone AS `phoneNumber`,
                    TIME_FORMAT(s.startTime, '%%H:%%i') AS `startTime`,
                    TIME_FORMAT(s.endTime, '%%H:%%i') AS `endTime`,
                    s.closedDays AS `closedDays`
                FROM Stores s
                WHERE s.status = '일반'
                AND s.storeId = %s
            """
            cursor.execute(store_details_sql, [store_id])
            store_details = cursor.fetchone()
            if not store_details:
                store_details = {}
            return jsonify(store_details)
    finally:
        conn.close()

@app.route('/storemenus', methods=['GET'])
@swag_from({
    'tags': ['Store Menus'],
    'parameters': [
        {
            'name': 'storeId',
            'in': 'query',
            'type': 'integer',
            'required': True,
            'description': 'ID of the store'
        }
    ],
    'responses': {
        200: {
            'description': 'Menus of the store',
            'schema': {
                'type': 'array',
                'items': {'type': 'object'}
            }
        }
    }
})
def store_menus():
    """
    Get menus of the store
    ---
    """
    store_id = request.args.get('storeId')
    if not store_id:
        return jsonify({'error': 'storeId parameter is required'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            menu_ranking_sql = """
                WITH RankedMenus AS (
                    SELECT 
                        m.menuId,
                        m.category AS `menuCategory`,
                        m.name AS `menuName`,
                        m.price AS `menuPrice`,
                        m.menuPictureUrl AS `menuPicture`,
                        COUNT(r.reviewId) AS `reviewCount`,
                        ROW_NUMBER() OVER (ORDER BY COUNT(r.reviewId) DESC) AS ranking
                    FROM Menu AS m
                    LEFT JOIN Reviews AS r ON m.menuId = r.menuId
                    WHERE m.status = '일반' AND m.storeId = %s
                    GROUP BY m.menuId
                )
                SELECT 
                    rm.menuCategory,
                    rm.menuName,
                    rm.menuPrice,
                    rm.menuPicture,
                    rm.reviewCount,
                    CASE 
                        WHEN rm.ranking <= 2 THEN '인기'
                        ELSE ''
                    END AS `popularity`
                FROM RankedMenus AS rm
                ORDER BY rm.ranking
            """
            cursor.execute(menu_ranking_sql, [store_id])
            menus = cursor.fetchall()
            return jsonify(menus)
    finally:
        conn.close()

# View 4 Route
@app.route('/menuinfo', methods=['GET'])
@swag_from({
    'tags': ['Menu Details'],
    'parameters': [
        {
            'name': 'menuId',
            'in': 'query',
            'type': 'integer',
            'required': True,
            'description': 'ID of the menu'
        }
    ],
    'responses': {
        200: {
            'description': 'Information about the menu',
            'schema': {'type': 'object'}
        }
    }
})
def menu_info():
    """
    Get information about a menu
    ---
    """
    menu_id = request.args.get('menuId')
    if not menu_id:
        return jsonify({'error': 'menuId parameter is required'}), 400
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            menu_info_sql = """
                SELECT 
                    m.name AS `menuName`,
                    m.menuPictureUrl AS `menuPicture`,
                    m.price AS `menuPrice`,
                    CASE 
                        WHEN r.totalReviews > 2 THEN '인기'
                        ELSE ''
                    END AS `popularity`,
                    r.totalReviews AS `reviewCount`
                FROM Menu AS m
                LEFT JOIN (
                    SELECT 
                        menuId,
                        COUNT(reviewId) AS totalReviews
                    FROM Reviews
                    WHERE status = '일반'
                    GROUP BY menuId
                ) AS r ON m.menuId = r.menuId
                WHERE m.status = '일반' AND m.menuId = %s
            """
            menu_option_sql = """
                SELECT 
                    mo.option AS `option`,
                    mo.content AS `content`,
                    mo.price AS `price`
                FROM MenuOption AS mo
                WHERE mo.status = '일반' AND mo.menuId = %s
            """
            cursor.execute(menu_info_sql, [menu_id])
            menu_info = cursor.fetchone()
            if not menu_info:
                menu_info = {}
            else:
                cursor.execute(menu_option_sql, [menu_id])
                menu_options = cursor.fetchall()
                menu_info['options'] = menu_options
            return jsonify(menu_info)
    finally:
        conn.close()

if __name__ == "__main__":
    app.run(debug=True, port=5000, host='0.0.0.0')