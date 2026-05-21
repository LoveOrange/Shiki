package com.example.shop.application.order.service;

import com.example.shop.application.order.dto.CreateOrderDTO;
import com.example.shop.application.order.dto.OrderDetailDTO;
import com.example.shop.domain.order.model.Order;
import com.example.shop.domain.order.repository.OrderRepository;
import com.example.shop.domain.order.support.CustomerCreditSupport;
import java.util.Optional;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class OrderServiceImpl implements OrderService {

    private final OrderRepository orderRepository;
    private final CustomerCreditSupport customerCreditSupport;

    public OrderServiceImpl(OrderRepository orderRepository,
                            CustomerCreditSupport customerCreditSupport) {
        this.orderRepository = orderRepository;
        this.customerCreditSupport = customerCreditSupport;
    }

    @Override
    @Transactional
    public Long createOrder(CreateOrderDTO command) {
        customerCreditSupport.ensureCustomerCanCreateOrder(command.getCustomerId());
        Order order = Order.create(command.getCustomerId(), command.getAmount());
        order.submit();
        orderRepository.save(order);
        return order.getOrderId();
    }

    @Override
    public OrderDetailDTO getOrderDetail(Long orderId) {
        Optional<Order> order = orderRepository.findById(orderId);
        if (!order.isPresent()) {
            return null;
        }
        return toDetail(order.get());
    }

    private OrderDetailDTO toDetail(Order order) {
        OrderDetailDTO detail = new OrderDetailDTO();
        detail.setOrderId(order.getOrderId());
        detail.setCustomerId(order.getCustomerId());
        detail.setAmount(order.getAmount());
        detail.setStatus(order.getStatus().name());
        return detail;
    }
}
