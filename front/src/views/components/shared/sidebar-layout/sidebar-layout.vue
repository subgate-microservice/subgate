<script setup lang="ts">
const headerHeight = "50px"
const sidebarWidth = "14rem"

</script>

<template>
  <div class="my-container">

    <div class="my-logo sticky-top">
      <slot name="logo">
        LOGO
      </slot>
    </div>

    <div class="my-sidebar sticky-top-for-sidebar">
      <slot name="sidebar">
        Sidebar
      </slot>
    </div>

    <div class="my-header sticky-top">
      <slot name="header">
        Topmenu
      </slot>
    </div>

    <div class="my-content">
      <div class="inner-content">
        <slot name="content">
          Content
        </slot>
      </div>
    </div>

    <div class="right-block"/>

  </div>
</template>


<style scoped>
.my-container {
  display: grid;
  grid-template-areas:
    "logo header right"
    "sidebar content right";
  grid-template-columns: v-bind(sidebarWidth) 1fr v-bind(sidebarWidth);
  grid-template-rows: v-bind(headerHeight) 1fr;
}

.my-logo {
  grid-area: logo;
  display: flex;
  align-items: center;
  background: var(--my-background);
  width: v-bind(sidebarWidth);
  height: v-bind(headerHeight);
}

.my-header {
  grid-area: header;
  display: flex;
  align-items: center;
  background: white;
  z-index: 1000;
  padding-left: 1.5rem;
}

.my-sidebar {
  grid-area: sidebar;
  width: v-bind(sidebarWidth);
  height: calc(100vh - v-bind(headerHeight));
  padding-top: 1.5rem;
  background: var(--my-background);
}

.my-content {
  grid-area: content;
  padding: 1.5rem 1.5rem 3rem;
  display: flex;
  justify-content: center;
  width: calc(100vw - 2 * v-bind(sidebarWidth));
  height: calc(100vh - v-bind(headerHeight));
}

.inner-content{
  max-width: 83rem;
  width: 100%;
}

.right-block{
  grid-area: right;
  width: v-bind(sidebarWidth);
}


.sticky-top {
  position: sticky;
  top: 0;
}

.sticky-top-for-sidebar {
  position: fixed;
  top: v-bind(headerHeight);
}


@media (max-width: 111rem) {
  .my-container {
    grid-template-areas:
      "logo header"
      "logo content";
    grid-template-columns: v-bind(sidebarWidth) 1fr;
  }

  .my-content {
    width: calc(100vw - v-bind(sidebarWidth));
  }


  .right-block {
    display: none;
  }

}

@media (max-width: 83rem) {
  .my-container {
    grid-template-areas:
      "logo"
      "content";
    grid-template-columns: 1fr;
  }

  .my-content {
    width: 100vw;
  }


  .right-block {
    display: none;
  }

  .my-sidebar{
    display: none;
  }

  .my-header{
    display: none;
  }

}
</style>
