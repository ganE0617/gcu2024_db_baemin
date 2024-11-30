
# API Descriptions

Below are detailed descriptions for each API endpoint in the application, including explanations of the SQL queries used.

---

## 1. `/photo/<path:filename>` - Serve Photo

**Method:** `GET`

**Description:**

Serves photo files from the server's `PHOTO_DIR`. When a request is made with a specific filename, the server checks if the file exists in the directory and serves it if found. If the file does not exist, a 404 error is returned.

**SQL Query:** None (This endpoint does not interact with the database.)

---

## 2. `/` - Echo Call

**Method:** `GET`

**Description:**

A simple endpoint that returns `'Hello, World'` when accessed. It can be used to verify that the server is running.

**SQL Query:** None (This endpoint does not interact with the database.)

---

## 3. `/samecategory` - Get Stores in the Same Category

**Method:** `GET`

**Parameters:**

- `category` (string, required): The category of stores to fetch.

**Description:**

Retrieves a list of stores that belong to the specified category. The response includes store details, associated menus, and the current order status based on the store's operating hours adjusted to the Asia/Seoul timezone (+9:00).

**SQL Queries:**

- **Store Query:**

  ```sql
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
  GROUP BY s.storeId
  ```

  - Retrieves active stores (`s.status = '일반'`) in the specified category.
  - Joins with `Coupons` to check for active coupons.
  - Groups by `storeId` to aggregate coupon information.

- **Menu Query:**

  ```sql
  SELECT 
      m.storeId, m.name AS menuName, m.price AS menuPrice, m.menuPictureUrl
  FROM Menu m
  WHERE m.status = '일반'
  ```

  - Retrieves all active menus (`m.status = '일반'`) across stores.

---

## 4. `/mindeliverytime` - Get Stores Sorted by Minimum Delivery Time

**Method:** `GET`

**Parameters:**

- `category` (string, required): The category of stores to fetch.

**Description:**

Fetches a list of stores in the specified category, sorted by their minimum delivery time in ascending order. Includes store details, associated menus, and current order status.

**SQL Queries:**

- **Store Query:**

  Same as in `/samecategory`, but with an added `ORDER BY` clause:

  ```sql
  ORDER BY s.minDeliveryTime ASC
  ```

- **Menu Query:**

  Same as in `/samecategory`.

---

## 5. `/mindeliverytip` - Get Stores Sorted by Minimum Delivery Tip

**Method:** `GET`

**Parameters:**

- `category` (string, required): The category of stores to fetch.

**Description:**

Retrieves stores in the specified category, sorted by their minimum delivery tip in ascending order. The response includes store details, menus, and order status.

**SQL Queries:**

- **Store Query:**

  Similar to `/samecategory`, with the following `ORDER BY` clause:

  ```sql
  ORDER BY s.minDeliveryTip ASC
  ```

- **Menu Query:**

  Same as in `/samecategory`.

---

## 6. `/highestrating` - Get Stores Sorted by Highest Rating

**Method:** `GET`

**Parameters:**

- `category` (string, required): The category of stores to fetch.

**Description:**

Provides a list of stores in the specified category, sorted by their rating in descending order. Includes detailed store information, menus, and computes order status based on the current time in Asia/Seoul timezone.

**SQL Queries:**

- **Store Query:**

  Similar to `/samecategory`, with the following `ORDER BY` clause:

  ```sql
  ORDER BY s.rating DESC
  ```

- **Menu Query:**

  Same as in `/samecategory`.

---

## 7. `/couponstores` - Get Stores Offering Coupons

**Method:** `GET`

**Parameters:**

- `category` (string, required): The category of stores to fetch that offer coupons.

**Description:**

Fetches stores within the specified category that currently have active coupons. The response includes store details, menus, and order status.

**SQL Queries:**

- **Store Query:**

  Similar to `/samecategory`, but includes an additional filter to only select stores with active coupons:

  ```sql
  AND c.status = '일반'
  ```

- **Menu Query:**

  Same as in `/samecategory`.

---

## 8. `/storeinfo` - Get Store Information

**Method:** `GET`

**Parameters:**

- `storeId` (integer, required): The ID of the store.

**Description:**

Provides detailed information about a specific store, including its picture, name, rating, review count, delivery tips, minimum order price, delivery times, description, and any available coupons.

**SQL Query:**

- **Store Information Query:**

  ```sql
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
  ```

  - Retrieves store details for the specified `storeId`.
  - Joins with `Coupons` to include active coupon information.

---

## 9. `/storedetails` - Get Detailed Store Information

**Method:** `GET`

**Parameters:**

- `storeId` (integer, required): The ID of the store.

**Description:**

Returns additional details about a store, such as its address, phone number, operating hours, and closed days.

**SQL Query:**

- **Store Details Query:**

  ```sql
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
  ```

  - Retrieves specific details for the given `storeId`.
  - Formats the start and end times to 'HH:MM'.

---

## 10. `/storemenus` - Get Menus of a Store

**Method:** `GET`

**Parameters:**

- `storeId` (integer, required): The ID of the store.

**Description:**

Fetches the menus offered by the specified store. The menus are ranked based on the number of reviews and marked as '인기' (popular) if they are among the top two.

**SQL Query:**

- **Menu Ranking Query:**

  ```sql
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
  ```

  - Uses a Common Table Expression (CTE) to rank menus based on review count.
  - Marks the top two menus as '인기' (popular).

---

## 11. `/menuinfo` - Get Information About a Menu

**Method:** `GET`

**Parameters:**

- `menuId` (integer, required): The ID of the menu.

**Description:**

Provides detailed information about a specific menu item, including its name, picture, price, popularity status, review count, and available options.

**SQL Queries:**

- **Menu Information Query:**

  ```sql
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
  ```

  - Retrieves menu details for the specified `menuId`.
  - Determines popularity based on the number of reviews.

- **Menu Options Query:**

  ```sql
  SELECT 
      mo.option AS `option`,
      mo.content AS `content`,
      mo.price AS `price`
  FROM MenuOption AS mo
  WHERE mo.status = '일반' AND mo.menuId = %s
  ```

  - Fetches available options for the menu item.
