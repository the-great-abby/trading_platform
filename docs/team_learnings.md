# Team Learnings & Preferences

## 🤝 **Working Style Preferences**

### **Abby's Preferences:**
- **Direct Communication**: Prefers straightforward feedback over excessive agreement
- **Container-Only Development**: Python should only run in containers, not locally
- **Resource Conscious**: Prefers minimal resource allocation for development
- **Practical Approach**: Focus on what works now, not theoretical perfection
- **Testing Priority**: Recognizes the critical lack of tests in the system

### **AI Assistant Preferences:**
- **Proactive Problem Solving**: Should identify and fix issues without being asked
- **Direct Feedback**: Should provide honest assessment, not just agreement
- **Practical Solutions**: Focus on immediate, actionable improvements
- **Documentation**: Should document learnings and decisions for future reference

## 📚 **Key Learnings from Our Work**

### **Technical Learnings:**
1. **Port Standardization**: External ports should use 11000-11999 range for security
2. **Container-Only Development**: All development should happen in containers
3. **Testing Gap**: The system has critical lack of comprehensive tests
4. **Syntax Errors**: RabbitMQ service has indentation issues that need fixing
5. **Resource Optimization**: Services should use minimal resources in development

### **Process Learnings:**
1. **Immediate Logging**: Log progress, learnings, and blockers as they happen
2. **Differential Coverage**: Use this technique for quick debugging
3. **Risk-Based Testing**: Focus on critical areas first (trading engine, risk management)
4. **Simple Tools**: Prefer simple, practical tools over complex systems

### **Communication Learnings:**
1. **Direct Feedback**: Prefer honest assessment over excessive praise
2. **Quick Sync**: Regular status updates and blocker sharing
3. **Knowledge Sharing**: Document discoveries immediately
4. **Practical Focus**: Focus on what works now, not theoretical improvements

## 🎯 **Current Priorities**

### **Immediate (This Week):**
- [ ] Fix RabbitMQ syntax errors
- [ ] Set up basic testing infrastructure
- [ ] Implement differential coverage debugging
- [ ] Focus on critical areas: trading engine, risk management

### **Short Term (Next 2 Weeks):**
- [ ] Comprehensive testing for critical services
- [ ] Improve documentation
- [ ] Optimize resource usage
- [ ] Implement monitoring and alerting

### **Medium Term (Next Month):**
- [ ] Complete test coverage for all critical services
- [ ] Performance optimization
- [ ] Security hardening
- [ ] Deployment automation

## 🚨 **Known Issues & Blockers**

### **Critical Issues:**
1. **RabbitMQ Syntax Error**: Indentation error in `rabbitmq_service.py` line 97
2. **Lack of Tests**: Most services have no test coverage
3. **Resource Usage**: Services using too much memory/CPU in development
4. **Port Security**: Some services using standard ports externally

### **Technical Debt:**
1. **Legacy Code**: Many services lack proper testability
2. **Documentation**: Incomplete or outdated documentation
3. **Monitoring**: Limited observability into system health
4. **Security**: Need to review and harden security measures

## 💡 **Best Practices We've Established**

### **Development Workflow:**
1. **Container-First**: Always develop in containers
2. **Test-Driven**: Write tests for new features
3. **Documentation**: Update docs as we work
4. **Incremental**: Make small, focused improvements

### **Communication:**
1. **Immediate Logging**: Log progress and blockers right away
2. **Direct Feedback**: Be honest about issues and solutions
3. **Knowledge Sharing**: Share learnings immediately
4. **Quick Sync**: Regular status updates

### **Quality Assurance:**
1. **Differential Coverage**: Use for quick debugging
2. **Risk-Based Testing**: Focus on critical areas first
3. **Simple Tools**: Prefer practical over perfect
4. **Continuous Improvement**: Small, regular improvements

## 📊 **Success Metrics**

### **Technical Metrics:**
- **Test Coverage**: Target 80%+ for critical services
- **System Reliability**: 99.9%+ uptime
- **Resource Usage**: <50% of available resources
- **Security**: Zero critical vulnerabilities

### **Process Metrics:**
- **Time to Fix**: <2 hours for critical bugs
- **Knowledge Sharing**: 100% of discoveries documented
- **Blocker Resolution**: <24 hours for non-critical blockers
- **Documentation**: 100% of new features documented

## 🔄 **How to Use This Document**

### **For New Sessions:**
1. **Review Priorities**: Check current priorities and blockers
2. **Update Learnings**: Add new insights and preferences
3. **Track Progress**: Update completed items
4. **Share Context**: Use this to quickly get up to speed

### **For Decision Making:**
1. **Check Preferences**: Ensure decisions align with our preferences
2. **Consider Learnings**: Apply past learnings to new situations
3. **Update Document**: Record new decisions and their rationale
4. **Share Changes**: Communicate updates to the team

---

*Last Updated: [Current Date]*
*Next Review: [Weekly]* 