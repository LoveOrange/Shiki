package com.example.shop.domain.order.model;

import java.math.BigDecimal;

public class Order {

    private Long orderId;
    private Long customerId;
    private BigDecimal amount;
    private OrderStatusEnum status;
    private Integer version;

    public static Order create(Long customerId, BigDecimal amount) {
        Order order = new Order();
        order.customerId = customerId;
        order.amount = amount;
        order.status = OrderStatusEnum.INIT;
        order.version = 0;
        return order;
    }

    public void submit() {
        if (status != OrderStatusEnum.INIT) {
            throw new IllegalStateException("Order state cannot be submitted");
        }
        status = OrderStatusEnum.SUBMITTED;
    }

    public Long getOrderId() {
        return orderId;
    }

    public void setOrderId(Long orderId) {
        this.orderId = orderId;
    }

    public Long getCustomerId() {
        return customerId;
    }

    public void setCustomerId(Long customerId) {
        this.customerId = customerId;
    }

    public BigDecimal getAmount() {
        return amount;
    }

    public void setAmount(BigDecimal amount) {
        this.amount = amount;
    }

    public OrderStatusEnum getStatus() {
        return status;
    }

    public void setStatus(OrderStatusEnum status) {
        this.status = status;
    }

    public Integer getVersion() {
        return version;
    }

    public void setVersion(Integer version) {
        this.version = version;
    }
}
