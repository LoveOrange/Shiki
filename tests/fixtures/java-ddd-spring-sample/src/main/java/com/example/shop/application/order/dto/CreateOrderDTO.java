package com.example.shop.application.order.dto;

import java.math.BigDecimal;

public class CreateOrderDTO {

    private Long customerId;
    private BigDecimal amount;

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
}
