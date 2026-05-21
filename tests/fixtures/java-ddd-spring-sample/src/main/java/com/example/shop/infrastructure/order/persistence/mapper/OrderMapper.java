package com.example.shop.infrastructure.order.persistence.mapper;

import com.example.shop.infrastructure.order.persistence.po.OrderPO;

public interface OrderMapper {

    OrderPO selectById(Long orderId);

    void insert(OrderPO orderPO);
}
