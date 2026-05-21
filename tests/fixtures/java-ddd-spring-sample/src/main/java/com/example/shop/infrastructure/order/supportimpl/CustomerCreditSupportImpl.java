package com.example.shop.infrastructure.order.supportimpl;

import com.example.shop.domain.order.support.CustomerCreditSupport;
import org.springframework.stereotype.Component;

@Component
public class CustomerCreditSupportImpl implements CustomerCreditSupport {

    @Override
    public void ensureCustomerCanCreateOrder(Long customerId) {
        if (customerId == null) {
            throw new IllegalArgumentException("Customer id is required");
        }
    }
}
