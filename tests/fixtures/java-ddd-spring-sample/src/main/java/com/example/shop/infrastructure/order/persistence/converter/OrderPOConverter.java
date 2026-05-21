package com.example.shop.infrastructure.order.persistence.converter;

import com.example.shop.domain.order.model.Order;
import com.example.shop.domain.order.model.OrderStatusEnum;
import com.example.shop.infrastructure.order.persistence.po.OrderPO;
import org.springframework.stereotype.Component;

@Component
public class OrderPOConverter {

    public Order toEntity(OrderPO orderPO) {
        if (orderPO == null) {
            return null;
        }
        Order order = new Order();
        order.setOrderId(orderPO.getOrderId());
        order.setCustomerId(orderPO.getCustomerId());
        order.setAmount(orderPO.getAmount());
        order.setStatus(OrderStatusEnum.valueOf(orderPO.getStatus()));
        order.setVersion(orderPO.getVersion());
        return order;
    }

    public OrderPO toPO(Order order) {
        if (order == null) {
            return null;
        }
        OrderPO orderPO = new OrderPO();
        orderPO.setOrderId(order.getOrderId());
        orderPO.setCustomerId(order.getCustomerId());
        orderPO.setAmount(order.getAmount());
        orderPO.setStatus(order.getStatus().name());
        orderPO.setVersion(order.getVersion());
        return orderPO;
    }
}
