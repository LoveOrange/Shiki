package com.example.shop.domain.order.repository;

import com.example.shop.domain.order.model.Order;
import java.util.Optional;

public interface OrderRepository {

    Optional<Order> findById(Long orderId);

    void save(Order order);
}
