// JavaScript code to handle the category and order option selection
document.getElementById('category').addEventListener('change', function() {
    fetchStores();
});

document.getElementById('orderOption').addEventListener('change', function() {
    fetchStores();
});

function fetchStores() {
    var category = document.getElementById('category').value;
    var orderOption = document.getElementById('orderOption').value;

    if (category) {
        // Build the API URL based on the selected order option
        var apiUrl = '/' + orderOption + '?category=' + encodeURIComponent(category);

        // Make an AJAX request to the API
        fetch(apiUrl)
            .then(function(response) {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(function(data) {
                displayResults(data);
            })
            .catch(function(error) {
                console.error('Error fetching data:', error);
                document.getElementById('results').innerHTML = '<p>데이터를 가져오는 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.</p>';
            });
    } else {
        document.getElementById('results').innerHTML = '';
    }
}

function displayResults(stores) {
    var resultsContainer = document.getElementById('results');
    resultsContainer.innerHTML = ''; // Clear previous results

    if (stores.length === 0) {
        resultsContainer.innerHTML = '<p>해당 카테고리의 가게가 없습니다.</p>';
        return;
    }

    stores.forEach(function(store) {
        // Create store container
        var storeDiv = document.createElement('div');
        storeDiv.className = 'store-container';

        // Store header with basic info
        var storeHeader = document.createElement('div');
        storeHeader.className = 'store-header';

        // Store basic details
        var storeDetails = document.createElement('div');
        storeDetails.className = 'store-details';

        var storeName = document.createElement('h2');
        storeName.textContent = store.storeName;

        var storeInfo = document.createElement('p');
        storeInfo.innerHTML = 
            '<strong>⭐ ' + store.rating + '</strong> (' + store.reviewCount + ')\n' +
            ' | 배달시간: ' + store.minDeliveryTime + '~' + store.maxDeliveryTime + '분\n' +
            ' | 배달팁: ' + store.minDeliveryTip + '~' + store.maxDeliveryTip + '원';

        storeDetails.appendChild(storeName);
        storeDetails.appendChild(storeInfo);

        storeHeader.appendChild(storeDetails);

        storeDiv.appendChild(storeHeader);

        // Display menus
        var menusDiv = document.createElement('div');
        menusDiv.className = 'menus';

        store.menus.forEach(function(menu) {
            var menuItemDiv = document.createElement('div');
            menuItemDiv.className = 'menu-item';
            menuItemDiv.setAttribute('data-menu-id', menu.menuId);

            var menuImage = document.createElement('img');
            // Use the menuPictureUrl as is, assuming it's a relative path
            menuImage.src = menu.menuPictureUrl;
            menuImage.alt = menu.menuName;

            var menuName = document.createElement('p');
            menuName.className = 'menu-name';
            menuName.textContent = menu.menuName;

            var menuPrice = document.createElement('p');
            menuPrice.className = 'menu-price';
            menuPrice.textContent = menu.menuPrice.toLocaleString() + '원';

            menuItemDiv.appendChild(menuImage);
            menuItemDiv.appendChild(menuName);
            menuItemDiv.appendChild(menuPrice);

            // Add click event listener to menu item
            menuItemDiv.addEventListener('click', function() {
                var menuId = this.getAttribute('data-menu-id');
                fetchMenuInfo(menuId);
            });

            menusDiv.appendChild(menuItemDiv);
        });

        storeDiv.appendChild(menusDiv);

        resultsContainer.appendChild(storeDiv);
    });
}

function fetchMenuInfo(menuId) {
    var apiUrl = '/menuinfo?menuId=' + encodeURIComponent(menuId);

    fetch(apiUrl)
        .then(function(response) {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(function(data) {
            displayMenuInfo(data);
        })
        .catch(function(error) {
            console.error('Error fetching menu info:', error);
            alert('메뉴 정보를 가져오는 중 오류가 발생했습니다.');
        });
}

function displayMenuInfo(menu) {
    var modal = document.getElementById('menu-modal');
    var modalContent = document.getElementById('menu-details');

    modalContent.innerHTML = ''; // Clear previous content

    var menuName = document.createElement('h2');
    menuName.textContent = menu.menuName;

    var menuImage = document.createElement('img');
    menuImage.src = menu.menuPicture;
    menuImage.alt = menu.menuName;

    var menuPrice = document.createElement('p');
    menuPrice.innerHTML = '<strong>가격:</strong> ' + menu.menuPrice.toLocaleString() + '원';

    var reviewCount = document.createElement('p');
    reviewCount.innerHTML = '<strong>리뷰 수:</strong> ' + (menu.reviewCount || 0);

    modalContent.appendChild(menuName);
    modalContent.appendChild(menuImage);
    modalContent.appendChild(menuPrice);
    modalContent.appendChild(reviewCount);

    // Display options if available
    if (menu.options && menu.options.length > 0) {
        var optionsByGroup = {};

        menu.options.forEach(function(option) {
            if (!optionsByGroup[option.option]) {
                optionsByGroup[option.option] = [];
            }
            optionsByGroup[option.option].push(option);
        });

        for (var optionGroup in optionsByGroup) {
            var groupDiv = document.createElement('div');
            groupDiv.className = 'option-group';

            var groupTitle = document.createElement('h3');
            groupTitle.textContent = optionGroup;

            groupDiv.appendChild(groupTitle);

            optionsByGroup[optionGroup].forEach(function(option) {
                var optionItem = document.createElement('div');
                optionItem.className = 'option-item';

                var optionContent = document.createElement('p');
                optionContent.textContent = option.content + ' (' + (option.price > 0 ? '+' + option.price.toLocaleString() + '원' : '무료') + ')';

                optionItem.appendChild(optionContent);
                groupDiv.appendChild(optionItem);
            });

            modalContent.appendChild(groupDiv);
        }
    }

    // Show the modal
    modal.style.display = 'block';
}

// Close the modal when the close button is clicked
document.getElementById('modal-close').addEventListener('click', function() {
    document.getElementById('menu-modal').style.display = 'none';
});

// Close the modal when clicking outside the modal content
window.addEventListener('click', function(event) {
    var modal = document.getElementById('menu-modal');
    if (event.target == modal) {
        modal.style.display = 'none';
    }
});