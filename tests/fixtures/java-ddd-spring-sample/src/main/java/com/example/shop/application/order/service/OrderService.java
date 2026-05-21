package com.example.shop.application.order.service;

import com.example.shop.application.order.dto.CreateOrderDTO;
import com.example.shop.application.order.dto.OrderDetailDTO;

public interface OrderService {

    Long createOrder(CreateOrderDTO command);

    OrderDetailDTO getOrderDetail(Long orderId);
}
