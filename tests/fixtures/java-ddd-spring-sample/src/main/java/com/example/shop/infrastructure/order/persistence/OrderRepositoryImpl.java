package com.example.shop.infrastructure.order.persistence;

import com.example.shop.domain.order.model.Order;
import com.example.shop.domain.order.repository.OrderRepository;
import com.example.shop.infrastructure.order.persistence.converter.OrderPOConverter;
import com.example.shop.infrastructure.order.persistence.mapper.OrderMapper;
import com.example.shop.infrastructure.order.persistence.po.OrderPO;
import java.util.Optional;
import org.springframework.stereotype.Repository;

@Repository
public class OrderRepositoryImpl implements OrderRepository {

    private final OrderMapper orderMapper;
    private final OrderPOConverter orderPOConverter;

    public OrderRepositoryImpl(OrderMapper orderMapper, OrderPOConverter orderPOConverter) {
        this.orderMapper = orderMapper;
        this.orderPOConverter = orderPOConverter;
    }

    @Override
    public Optional<Order> findById(Long orderId) {
        OrderPO orderPO = orderMapper.selectById(orderId);
        return Optional.ofNullable(orderPO).map(orderPOConverter::toEntity);
    }

    @Override
    public void save(Order order) {
        orderMapper.insert(orderPOConverter.toPO(order));
    }
}
