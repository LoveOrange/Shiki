package com.example.shop.adapter.order.web;

import com.example.shop.application.order.dto.CreateOrderDTO;
import com.example.shop.application.order.dto.OrderDetailDTO;
import com.example.shop.application.order.service.OrderService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {

    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @PostMapping
    public Long create(@RequestBody CreateOrderDTO command) {
        return orderService.createOrder(command);
    }

    @GetMapping("/{orderId}")
    public OrderDetailDTO detail(@PathVariable Long orderId) {
        return orderService.getOrderDetail(orderId);
    }
}
